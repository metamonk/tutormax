"""
Database query optimization utilities.

Provides tools for:
- Query analysis with EXPLAIN
- Index recommendations
- Slow query logging
- Query performance monitoring
"""

import logging
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query


logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Query optimization and analysis utilities.
    """

    def __init__(self):
        """Initialize query optimizer."""
        self.slow_query_threshold_ms = 100  # Log queries slower than 100ms
        self.query_stats: Dict[str, Any] = {
            "total_queries": 0,
            "slow_queries": 0,
            "total_time_ms": 0,
            "slowest_queries": []
        }

    async def explain_query(
        self,
        session: AsyncSession,
        query: str,
        analyze: bool = True
    ) -> Dict[str, Any]:
        """
        Run EXPLAIN (ANALYZE) on a query.

        Args:
            session: Database session
            query: SQL query to analyze
            analyze: Include ANALYZE for actual execution timing

        Returns:
            Query plan and statistics
        """
        explain_cmd = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)" if analyze else "EXPLAIN (FORMAT JSON)"
        full_query = f"{explain_cmd} {query}"

        try:
            result = await session.execute(text(full_query))
            plan = result.scalar()

            logger.info(f"Query plan: {plan}")
            return {
                "query": query,
                "plan": plan,
                "analyzed": analyze,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to explain query: {e}")
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def analyze_slow_queries(
        self,
        session: AsyncSession,
        min_duration_ms: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch slow queries from pg_stat_statements.

        Requires pg_stat_statements extension to be enabled.

        Args:
            session: Database session
            min_duration_ms: Minimum query duration in milliseconds

        Returns:
            List of slow queries
        """
        query = text("""
            SELECT
                query,
                calls,
                total_exec_time / 1000 as total_time_seconds,
                mean_exec_time as avg_time_ms,
                max_exec_time as max_time_ms,
                stddev_exec_time as stddev_time_ms,
                rows
            FROM pg_stat_statements
            WHERE mean_exec_time > :min_duration
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """)

        try:
            result = await session.execute(query, {"min_duration": min_duration_ms})
            rows = result.fetchall()

            slow_queries = []
            for row in rows:
                slow_queries.append({
                    "query": row[0],
                    "calls": row[1],
                    "total_time_seconds": float(row[2]),
                    "avg_time_ms": float(row[3]),
                    "max_time_ms": float(row[4]),
                    "stddev_time_ms": float(row[5]),
                    "rows": row[6]
                })

            return slow_queries
        except Exception as e:
            logger.error(f"Failed to fetch slow queries: {e}")
            return []

    async def get_table_indexes(
        self,
        session: AsyncSession,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get all indexes for a table.

        Args:
            session: Database session
            table_name: Table name

        Returns:
            List of indexes
        """
        query = text("""
            SELECT
                indexname,
                indexdef,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as size
            FROM pg_indexes
            WHERE tablename = :table_name
            ORDER BY indexname
        """)

        try:
            result = await session.execute(query, {"table_name": table_name})
            rows = result.fetchall()

            indexes = []
            for row in rows:
                indexes.append({
                    "name": row[0],
                    "definition": row[1],
                    "size": row[2]
                })

            return indexes
        except Exception as e:
            logger.error(f"Failed to fetch indexes for {table_name}: {e}")
            return []

    async def get_table_stats(
        self,
        session: AsyncSession,
        table_name: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a table.

        Args:
            session: Database session
            table_name: Table name

        Returns:
            Table statistics
        """
        query = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as indexes_size,
                n_live_tup as row_count,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE tablename = :table_name
        """)

        try:
            result = await session.execute(query, {"table_name": table_name})
            row = result.fetchone()

            if row:
                return {
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "table_size": row[3],
                    "indexes_size": row[4],
                    "row_count": row[5],
                    "dead_rows": row[6],
                    "last_vacuum": row[7].isoformat() if row[7] else None,
                    "last_autovacuum": row[8].isoformat() if row[8] else None,
                    "last_analyze": row[9].isoformat() if row[9] else None,
                    "last_autoanalyze": row[10].isoformat() if row[10] else None
                }
            else:
                return {"error": f"Table {table_name} not found"}
        except Exception as e:
            logger.error(f"Failed to fetch stats for {table_name}: {e}")
            return {"error": str(e)}

    async def suggest_indexes(
        self,
        session: AsyncSession,
        table_name: str
    ) -> List[str]:
        """
        Suggest indexes based on missing index statistics.

        Args:
            session: Database session
            table_name: Table name

        Returns:
            List of suggested index DDL statements
        """
        # This is a simplified version - production would use pg_qualstats or similar
        query = text("""
            SELECT
                schemaname,
                tablename,
                attname
            FROM pg_stats
            WHERE tablename = :table_name
              AND n_distinct > 100  -- High cardinality columns
              AND null_frac < 0.5   -- Not too many nulls
            ORDER BY n_distinct DESC
            LIMIT 10
        """)

        try:
            result = await session.execute(query, {"table_name": table_name})
            rows = result.fetchall()

            # Get existing indexes
            existing_indexes = await self.get_table_indexes(session, table_name)
            existing_columns = set()
            for idx in existing_indexes:
                # Extract column names from index definition
                if "(" in idx["definition"] and ")" in idx["definition"]:
                    cols = idx["definition"].split("(")[1].split(")")[0]
                    existing_columns.update(col.strip() for col in cols.split(","))

            suggestions = []
            for row in rows:
                schema, table, column = row
                if column not in existing_columns:
                    suggestions.append(
                        f"CREATE INDEX idx_{table}_{column} ON {schema}.{table} ({column});"
                    )

            return suggestions
        except Exception as e:
            logger.error(f"Failed to suggest indexes for {table_name}: {e}")
            return []

    @asynccontextmanager
    async def track_query_time(self, query_name: str):
        """
        Context manager to track query execution time.

        Args:
            query_name: Name/identifier for the query

        Usage:
            async with optimizer.track_query_time("get_tutor_stats"):
                result = await session.execute(query)
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.query_stats["total_queries"] += 1
            self.query_stats["total_time_ms"] += duration_ms

            if duration_ms > self.slow_query_threshold_ms:
                self.query_stats["slow_queries"] += 1
                logger.warning(
                    f"Slow query detected: {query_name} took {duration_ms:.2f}ms"
                )

                # Track slowest queries
                self.query_stats["slowest_queries"].append({
                    "name": query_name,
                    "duration_ms": duration_ms,
                    "timestamp": datetime.now().isoformat()
                })

                # Keep only top 20 slowest
                self.query_stats["slowest_queries"].sort(
                    key=lambda x: x["duration_ms"],
                    reverse=True
                )
                self.query_stats["slowest_queries"] = self.query_stats["slowest_queries"][:20]

    def get_query_stats(self) -> Dict[str, Any]:
        """
        Get query performance statistics.

        Returns:
            Query statistics
        """
        total_queries = self.query_stats["total_queries"]
        avg_time = (
            self.query_stats["total_time_ms"] / total_queries
            if total_queries > 0
            else 0
        )

        return {
            "total_queries": total_queries,
            "slow_queries": self.query_stats["slow_queries"],
            "slow_query_rate": (
                self.query_stats["slow_queries"] / total_queries * 100
                if total_queries > 0
                else 0
            ),
            "total_time_ms": self.query_stats["total_time_ms"],
            "avg_time_ms": avg_time,
            "slowest_queries": self.query_stats["slowest_queries"]
        }

    def reset_stats(self) -> None:
        """Reset query statistics."""
        self.query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "total_time_ms": 0,
            "slowest_queries": []
        }


# Global query optimizer instance
query_optimizer = QueryOptimizer()


async def get_query_optimizer() -> QueryOptimizer:
    """
    Dependency injection for FastAPI.

    Returns:
        QueryOptimizer instance
    """
    return query_optimizer
