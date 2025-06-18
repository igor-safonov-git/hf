#!/usr/bin/env python3
"""
Download all Huntflow data via API and store in SQLite database.
This allows working with the Huntflow schema without constant API calls.
"""

import asyncio
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class HuntflowDataDownloader:
    def __init__(self):
        self.token = os.getenv("HF_TOKEN")
        self.account_id = os.getenv("ACC_ID")
        self.base_url = "https://api.huntflow.ru"
        self.db_path = "huntflow_cache.db"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.token or not self.account_id:
            raise ValueError("HF_TOKEN and ACC_ID must be set in .env file")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self._init_database()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _init_database(self):
        """Initialize SQLite database with tables for all Huntflow entities."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Meta table for tracking download status
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS download_meta (
                entity_type TEXT PRIMARY KEY,
                last_downloaded TIMESTAMP,
                record_count INTEGER,
                raw_data TEXT
            )
        """)
        
        # Core entities tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id INTEGER PRIMARY KEY,
                position TEXT,
                status TEXT,
                created TIMESTAMP,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                created TIMESTAMP,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applicant_logs (
                id INTEGER PRIMARY KEY,
                applicant_id INTEGER,
                vacancy_id INTEGER,
                status_id INTEGER,
                created TIMESTAMP,
                raw_data TEXT,
                FOREIGN KEY (applicant_id) REFERENCES applicants(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vacancy_statuses (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                order_number INTEGER,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS divisions (
                id INTEGER PRIMARY KEY,
                name TEXT,
                parent_id INTEGER,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY,
                name TEXT,
                parent_id INTEGER,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coworkers (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rejection_reasons (
                id INTEGER PRIMARY KEY,
                name TEXT,
                raw_data TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applicant_sources (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                raw_data TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Huntflow API."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        async with self.session.request(method, url, headers=headers, **kwargs) as response:
            if response.status == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                return await self._make_request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            return await response.json()
    
    async def _paginate_endpoint(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """Handle paginated endpoints."""
        all_items = []
        page = 1
        
        while True:
            current_params = {"count": 100, "page": page}
            if params:
                current_params.update(params)
            
            logger.info(f"Fetching {endpoint} page {page}")
            data = await self._make_request("GET", endpoint, params=current_params)
            
            items = data.get("items", [])
            if not items:
                break
            
            all_items.extend(items)
            
            # Check if more pages exist
            if len(items) < 100:
                break
            
            page += 1
            await asyncio.sleep(0.5)  # Be nice to the API
        
        return all_items
    
    def _save_to_db(self, table: str, items: List[Dict], special_handler=None):
        """Save items to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in items:
            if special_handler:
                special_handler(cursor, item)
            else:
                # Generic handler for simple entities
                raw_data = json.dumps(item, ensure_ascii=False)
                
                if table == "vacancies":
                    cursor.execute("""
                        INSERT OR REPLACE INTO vacancies (id, position, status, created, raw_data)
                        VALUES (?, ?, ?, ?, ?)
                    """, (item["id"], item.get("position"), item.get("status"), item.get("created"), raw_data))
                
                elif table == "applicants":
                    cursor.execute("""
                        INSERT OR REPLACE INTO applicants (id, first_name, last_name, email, phone, created, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item["id"], 
                        item.get("first_name"), 
                        item.get("last_name"),
                        item.get("email"),
                        item.get("phone"),
                        item.get("created"),
                        raw_data
                    ))
                
                elif table == "vacancy_statuses":
                    cursor.execute("""
                        INSERT OR REPLACE INTO vacancy_statuses (id, name, type, order_number, raw_data)
                        VALUES (?, ?, ?, ?, ?)
                    """, (item["id"], item.get("name"), item.get("type"), item.get("order"), raw_data))
                
                else:
                    # For simple entities with just id and name
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO {table} (id, name, raw_data)
                        VALUES (?, ?, ?)
                    """, (item["id"], item.get("name"), raw_data))
        
        # Update metadata
        cursor.execute("""
            INSERT OR REPLACE INTO download_meta (entity_type, last_downloaded, record_count, raw_data)
            VALUES (?, ?, ?, ?)
        """, (table, datetime.now().isoformat(), len(items), json.dumps({"count": len(items)})))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(items)} {table} to database")
    
    async def download_all(self, clean_start=True):
        """Download all data from Huntflow API."""
        if clean_start:
            # Clear existing data for a clean download
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            tables = ["applicant_logs", "applicants", "vacancies", "vacancy_statuses", 
                     "divisions", "regions", "coworkers", "rejection_reasons", 
                     "applicant_sources", "accounts", "download_meta"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()
            conn.close()
            logger.info("Cleared existing data for clean download")
        
        logger.info("Starting full Huntflow data download...")
        
        # 1. Download account info
        logger.info("Downloading account info...")
        accounts = await self._make_request("GET", "/v2/accounts")
        self._save_to_db("accounts", accounts.get("items", []))
        
        # 2. Download vacancy statuses (recruitment stages)
        logger.info("Downloading vacancy statuses...")
        statuses = await self._make_request("GET", f"/v2/accounts/{self.account_id}/vacancies/statuses")
        self._save_to_db("vacancy_statuses", statuses.get("items", []))
        
        # 3. Download divisions
        logger.info("Downloading divisions...")
        divisions = await self._make_request("GET", f"/v2/accounts/{self.account_id}/divisions")
        self._save_to_db("divisions", divisions.get("items", []))
        
        # 4. Download regions
        logger.info("Downloading regions...")
        regions = await self._make_request("GET", f"/v2/accounts/{self.account_id}/regions")
        self._save_to_db("regions", regions.get("items", []))
        
        # 5. Download coworkers
        logger.info("Downloading coworkers...")
        coworkers = await self._paginate_endpoint(f"/v2/accounts/{self.account_id}/coworkers")
        self._save_to_db("coworkers", coworkers)
        
        # 6. Download rejection reasons
        logger.info("Downloading rejection reasons...")
        rejection_reasons = await self._make_request("GET", f"/v2/accounts/{self.account_id}/rejection_reasons")
        self._save_to_db("rejection_reasons", rejection_reasons.get("items", []))
        
        # 7. Download applicant sources
        logger.info("Downloading applicant sources...")
        sources = await self._make_request("GET", f"/v2/accounts/{self.account_id}/applicants/sources")
        self._save_to_db("applicant_sources", sources.get("items", []))
        
        # 8. Download vacancies
        logger.info("Downloading vacancies...")
        vacancies = await self._paginate_endpoint(f"/v2/accounts/{self.account_id}/vacancies")
        self._save_to_db("vacancies", vacancies)
        
        # 9. Download applicants (this might be large)
        logger.info("Downloading applicants...")
        applicants = await self._paginate_endpoint(f"/v2/accounts/{self.account_id}/applicants/search")
        self._save_to_db("applicants", applicants)
        
        # 10. Download applicant logs for a sample (logs can be huge)
        logger.info("Downloading applicant logs (sample)...")
        await self._download_applicant_logs(applicants[:100])  # Sample first 100
        
        logger.info("Download completed!")
        self._print_summary()
    
    async def _download_applicant_logs(self, applicants: List[Dict]):
        """Download logs for given applicants."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        successful_logs = 0
        total_log_entries = 0
        
        for i, applicant in enumerate(applicants):
            if i % 20 == 0:
                logger.info(f"Processing applicant logs: {i}/{len(applicants)} ({i/len(applicants)*100:.0f}%)")
            
            try:
                logs = await self._make_request(
                    "GET", 
                    f"/v2/accounts/{self.account_id}/applicants/{applicant['id']}/logs"
                )
                
                items = logs.get("items", [])
                if isinstance(items, list):
                    successful_logs += 1
                    for log in items:
                        if isinstance(log, dict):
                            total_log_entries += 1
                            cursor.execute("""
                                INSERT OR REPLACE INTO applicant_logs 
                                (id, applicant_id, vacancy_id, status_id, created, raw_data)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                log.get("id"),
                                applicant["id"],
                                log.get("vacancy", {}).get("id") if log.get("vacancy") else None,
                                log.get("status", {}).get("id") if log.get("status") else None,
                                log.get("created"),
                                json.dumps(log, ensure_ascii=False)
                            ))
                
                await asyncio.sleep(0.3)  # Rate limiting
                
            except aiohttp.ClientResponseError as e:
                if e.status != 404:  # Ignore 404 errors (applicant might not have logs)
                    logger.warning(f"HTTP {e.status} for applicant {applicant['id']}")
            except Exception as e:
                logger.debug(f"Error for applicant {applicant['id']}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Downloaded logs from {successful_logs}/{len(applicants)} applicants ({total_log_entries} total log entries)")
    
    def _print_summary(self):
        """Print summary of downloaded data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*50)
        print("DOWNLOAD SUMMARY")
        print("="*50)
        
        tables = [
            "accounts", "vacancies", "applicants", "applicant_logs",
            "vacancy_statuses", "divisions", "regions", "coworkers",
            "rejection_reasons", "applicant_sources"
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT last_downloaded FROM download_meta WHERE entity_type = ?", 
                (table,)
            )
            result = cursor.fetchone()
            last_downloaded = result[0] if result else "Never"
            
            print(f"{table:20} {count:8} records  (Last: {last_downloaded})")
        
        print("="*50)
        print(f"Database saved to: {os.path.abspath(self.db_path)}")
        conn.close()


async def main():
    """Main entry point."""
    async with HuntflowDataDownloader() as downloader:
        await downloader.download_all()


if __name__ == "__main__":
    asyncio.run(main())