"""Initial migration: create tables and pgvector extension

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'support_agent', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('status', postgresql.ENUM('uploaded', 'processing', 'processed', 'failed', name='documentstatus'), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('filename'),
    )
    op.create_index(op.f('ix_documents_filename'), 'documents', ['filename'], unique=True)
    
    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'])
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding '
        'ON document_chunks USING hnsw (embedding vector_cosine_ops)'
    )
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('ai_active', 'escalated', 'human_active', 'resolved', name='conversationstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index(op.f('ix_conversations_session_id'), 'conversations', ['session_id'], unique=True)
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_type', postgresql.ENUM('customer', 'ai', 'agent', name='sendertype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'])
    
    # Create message_sources table
    op.create_table(
        'message_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_message_sources_message_id'), 'message_sources', ['message_id'])
    
    # Create escalations table
    op.create_table(
        'escalations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('open', 'in_progress', 'resolved', name='escalationstatus'), nullable=False),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id'),
    )
    op.create_index(op.f('ix_escalations_conversation_id'), 'escalations', ['conversation_id'], unique=True)


def downgrade() -> None:
    # Drop escalations table
    op.drop_index(op.f('ix_escalations_conversation_id'), table_name='escalations')
    op.drop_table('escalations')
    
    # Drop message_sources table
    op.drop_index(op.f('ix_message_sources_message_id'), table_name='message_sources')
    op.drop_table('message_sources')
    
    # Drop messages table
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_table('messages')
    
    # Drop conversations table
    op.drop_index(op.f('ix_conversations_session_id'), table_name='conversations')
    op.drop_table('conversations')
    
    # Drop document_chunks table
    op.execute('DROP INDEX IF EXISTS ix_document_chunks_embedding')
    op.drop_index(op.f('ix_document_chunks_document_id'), table_name='document_chunks')
    op.drop_table('document_chunks')
    
    # Drop documents table
    op.drop_index(op.f('ix_documents_filename'), table_name='documents')
    op.drop_table('documents')
    
    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS documentstatus')
    op.execute('DROP TYPE IF EXISTS conversationstatus')
    op.execute('DROP TYPE IF EXISTS sendertype')
    op.execute('DROP TYPE IF EXISTS escalationstatus')
