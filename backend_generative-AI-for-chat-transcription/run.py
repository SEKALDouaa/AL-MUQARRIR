from pyngrok import ngrok
from app import app  # Import the Flask app from app.py
import atexit
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

DB_PATH = "speaker_db.pkl"  # Adjust path if needed

def stop_tunnel(public_url):
    """Stop the ngrok tunnel."""
    try:
        ngrok.disconnect(public_url)
        print(f"Ngrok tunnel {public_url} has been closed.")
    except Exception as e:
        print(f"Error stopping tunnel {public_url}: {e}")

def kill_all_tunnels():
    """Kill all active ngrok tunnels."""
    try:
        ngrok.kill()
        print("✅ Ngrok agent and all tunnels have been forcefully closed.")
    except Exception as e:
        print(f"Error killing tunnels: {e}")

def remove_speaker_db():
    """Delete the speaker DB file on shutdown."""
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"🗑️  Removed speaker DB: {DB_PATH}")
        except Exception as e:
            print(f"Error removing {DB_PATH}: {e}")
    else:
        print(f"ℹ️  Speaker DB not found at shutdown: {DB_PATH}")

# Register cleanup handlers
atexit.register(kill_all_tunnels)
atexit.register(remove_speaker_db)

if __name__ == "__main__":
    # Set up ngrok authentication
    ngrok.set_auth_token(os.getenv("NGROK_TOKEN"))

    # Start ngrok tunnel
    public_url = ngrok.connect(5000, bind_tls=True).public_url
    print(f"🔗 Public URL: {public_url}")
    print("💡 Keep this cell running to maintain the tunnel.")

    try:
        # Run Flask in the main thread
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("Stopping server...")
        stop_tunnel(public_url)
        kill_all_tunnels()
        remove_speaker_db()
