#!/usr/bin/env python3
"""
FastAPI Metrics Monitoring System - Direct Runner
Run with: python3 main.py
"""
import sys
import os

# Ensure we can import from the app package
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if os.path.basename(current_dir) == 'app' else current_dir
sys.path.insert(0, project_root)

def main():
    """Main entry point for direct execution"""
    try:
        print("🔄 Loading FastAPI Metrics Monitoring System...")
        
        # Import required modules
        import uvicorn
        from app.main import app
        from app.config import settings
        
        print(f"✅ {settings.app_name} v{settings.app_version} loaded successfully!")
        print("=" * 60)
        print(f"🌐 Server: http://{settings.host}:{settings.port}")
        print(f"📊 Metrics: http://{settings.host}:{settings.port}/metrics")
        print(f"🏥 Health: http://{settings.host}:{settings.port}/health")
        print(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
        print("=" * 60)
        
        # Start the server
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Solutions:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Run from project root directory")
        print("3. Ensure virtual environment is activated")
        return 1
        
    except Exception as e:
        print(f"❌ Startup Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code or 0)
