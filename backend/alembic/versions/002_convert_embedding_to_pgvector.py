"""Convert the embedding column to the pgvector type.

The initial schema created this column as a PostgreSQL array on databases
where the pgvector SQLAlchemy type was not available during migration.
"""

from alembic import op


revision = "002_pgvector_embedding"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_type
                JOIN pg_namespace ON pg_namespace.oid = pg_type.typnamespace
                WHERE pg_namespace.nspname = 'public'
                  AND pg_type.typname = 'vector'
                  AND pg_type.typtype = 'd'
            ) THEN
                DROP DOMAIN public.vector;
            END IF;
        END $$
        """
    )
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    op.execute(
        """
        ALTER TABLE document_chunks
        ALTER COLUMN embedding TYPE vector(384)
        USING CASE
            WHEN embedding IS NULL THEN NULL
            ELSE ('[' || array_to_string(embedding, ',') || ']')::vector
        END
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE document_chunks
        ALTER COLUMN embedding TYPE double precision[]
        USING CASE
            WHEN embedding IS NULL THEN NULL
            ELSE string_to_array(trim(both '[]' from embedding::text), ',')::double precision[]
        END
        """
    )