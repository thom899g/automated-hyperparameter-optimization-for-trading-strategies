"""
System configuration and environment management
Critical: Centralized configuration to prevent import errors and ensure proper initialization
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize logging first to track system startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('hyperparameter_optimization.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str = "evolution-ecosystem-trading"
    collection_name: str = "trading_strategies"
    optimization_history: str = "optimization_history"
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not self.project_id or not self.collection_name:
            logger.error("Firebase configuration incomplete")
            return False
        return True

@dataclass
class OptimizationConfig:
    """Optimization algorithm configuration"""
    # Bayesian Optimization parameters
    n_initial_points: int = 10
    n_calls: int = 50
    random_state: int = 42
    acq_func: str = "gp_hedge"
    
    # Real-time adaptation
    optimization_frequency_minutes: int = 30
    max_optimization_time_minutes: int = 10
    performance_threshold: float = 0.05  # 5% improvement required
    
    def validate(self) -> bool:
        """Validate optimization configuration"""
        if self.n_calls < self.n_initial_points:
            logger.error("n_calls must be >= n_initial_points")
            return False
        if self.optimization_frequency_minutes <= 0:
            logger.error("Optimization frequency must be positive")
            return False
        return True

class SystemConfig:
    """Main system configuration manager"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.firebase: Optional[FirebaseConfig] = None
        self.optimization: Optional[OptimizationConfig] = None
        self.initialized = False
        self._db = None
        
        # Initialize immediately to prevent NameError
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize configuration from environment"""
        try:
            logger.info("Initializing system configuration")
            
            # Load environment variables
            env_vars = self._load_env_vars()
            
            # Initialize configurations
            self.firebase = FirebaseConfig(
                project_id=env_vars.get("FIREBASE_PROJECT_ID", "evolution-ecosystem-trading"),
                collection_name=env_vars.get("FIREBASE_COLLECTION", "trading_strategies")
            )
            
            self.optimization = OptimizationConfig(
                n_initial_points=int(env_vars.get("OPT_INITIAL_POINTS", "10")),
                n_calls=int(env_vars.get("OPT_N_CALLS", "50")),
                optimization_frequency_minutes=int(env_vars.get("OPT_FREQUENCY", "30"))
            )
            
            # Validate configurations
            if not self.firebase.validate():
                raise ValueError("Invalid Firebase configuration")
            if not self.optimization.validate():
                raise ValueError("Invalid optimization configuration")
            
            # Initialize Firebase
            self._init_firebase()
            
            self.initialized = True
            logger.info("System configuration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to