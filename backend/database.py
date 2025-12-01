"""Database management for detection logs"""
import sqlite3
import pandas as pd
from datetime import datetime
import config
import logging
import threading
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionDatabase:
    def __init__(self):
        self.db_path = config.DATABASE_PATH
        self.csv_path = config.CSV_LOG_PATH
        self.lock = threading.Lock()  # Thread safety
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error: {e}")
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize SQLite database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        class_name TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        bbox_x1 INTEGER,
                        bbox_y1 INTEGER,
                        bbox_x2 INTEGER,
                        bbox_y2 INTEGER,
                        frame_number INTEGER,
                        source TEXT,
                        tracking_id INTEGER
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        total_detections INTEGER,
                        unique_classes INTEGER,
                        fps REAL,
                        processing_time REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        alert_type TEXT,
                        message TEXT,
                        class_name TEXT,
                        count INTEGER
                    )
                ''')
                
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def log_detection(self, class_name, confidence, bbox, frame_number, source='webcam', tracking_id=None):
        """Log detection to database (thread-safe)"""
        if not isinstance(class_name, str) or not class_name.strip():
            logger.warning("Invalid class name received")
            return
        
        if not 0 <= confidence <= 1:
            logger.warning(f"Invalid confidence value: {confidence}")
            return
        
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    x1, y1, x2, y2 = bbox
                    
                    cursor.execute('''
                        INSERT INTO detections 
                        (class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, frame_number, source, tracking_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (class_name, confidence, int(x1), int(y1), int(x2), int(y2), frame_number, source, tracking_id))
                    
        except Exception as e:
            logger.error(f"Error logging detection: {e}")
    
    def log_alert(self, alert_type, message, class_name, count):
        """Log alert (thread-safe)"""
        if not isinstance(alert_type, str) or not alert_type.strip():
            logger.warning("Invalid alert type")
            return
        
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO alerts (alert_type, message, class_name, count)
                        VALUES (?, ?, ?, ?)
                    ''', (alert_type, message, class_name, count))
                    
        except Exception as e:
            logger.error(f"Error logging alert: {e}")
    
    def get_recent_detections(self, limit=100):
        """Get recent detections with better pagination"""
        try:
            limit = min(int(limit), 1000)  # Limit max results
            with self.get_connection() as conn:
                df = pd.read_sql_query(f'''
                    SELECT id, timestamp, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, 
                           frame_number, source, tracking_id 
                    FROM detections 
                    ORDER BY timestamp DESC, id DESC 
                    LIMIT ?
                ''', conn, params=(limit,))
                return df
        except Exception as e:
            logger.error(f"Error retrieving detections: {e}")
            return pd.DataFrame()
    
    def get_class_statistics(self):
        """Get detection count by class with confidence metrics"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query('''
                    SELECT class_name, 
                           COUNT(*) as count, 
                           AVG(confidence) as avg_confidence,
                           MIN(confidence) as min_confidence,
                           MAX(confidence) as max_confidence,
                           ROUND(AVG(confidence), 3) as confidence_score
                    FROM detections
                    GROUP BY class_name
                    ORDER BY count DESC
                ''', conn)
                return df
        except Exception as e:
            logger.error(f"Error retrieving class statistics: {e}")
            return pd.DataFrame()
    
    def get_recent_alerts(self, limit=10):
        """Get recent alerts"""
        try:
            limit = min(int(limit), 500)  # Limit max results
            with self.get_connection() as conn:
                df = pd.read_sql_query(f'''
                    SELECT * FROM alerts 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', conn, params=(limit,))
                return df
        except Exception as e:
            logger.error(f"Error retrieving alerts: {e}")
            return pd.DataFrame()
    
    def export_to_csv(self):
        """Export to CSV"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query('SELECT * FROM detections', conn)
                df.to_csv(self.csv_path, index=False)
                logger.info(f"Data exported to {self.csv_path}")
                return self.csv_path
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def clear_old_data(self, days=7):
        """Clear old data"""
        try:
            if not isinstance(days, int) or days < 0:
                logger.warning("Invalid days parameter")
                return
            
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        DELETE FROM detections 
                        WHERE timestamp < datetime('now', '-' || ? || ' days')
                    ''', (days,))
                    
                    logger.info(f"Cleared detections older than {days} days")
        except Exception as e:
            logger.error(f"Error clearing old data: {e}")
    
    def get_detections_by_class(self, class_name, limit=50):
        """Get detections for specific class"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query('''
                    SELECT * FROM detections 
                    WHERE class_name = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', conn, params=(class_name, limit))
                return df
        except Exception as e:
            logger.error(f"Error retrieving class detections: {e}")
            return pd.DataFrame()
    
    def get_detections_by_date_range(self, start_time, end_time):
        """Get detections within a date range"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query('''
                    SELECT * FROM detections 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                ''', conn, params=(start_time, end_time))
                return df
        except Exception as e:
            logger.error(f"Error retrieving detections by date range: {e}")
            return pd.DataFrame()
    
    def get_high_confidence_detections(self, min_confidence=0.8, limit=50):
        """Get detections with high confidence scores"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query('''
                    SELECT * FROM detections 
                    WHERE confidence >= ?
                    ORDER BY confidence DESC, timestamp DESC
                    LIMIT ?
                ''', conn, params=(min_confidence, limit))
                return df
        except Exception as e:
            logger.error(f"Error retrieving high confidence detections: {e}")
            return pd.DataFrame()
