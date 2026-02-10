import subprocess
import os
import sys

def run_script(script_name, args):
    """
    Executes a python script from the app/scripts directory.
    
    :param script_name: Name of the script (without .py)
    :param args: List of string arguments
    :return: Output of the script or error message
    """
    scripts_dir = os.path.join(os.getcwd(), "app", "scripts")
    script_path = os.path.join(scripts_dir, f"{script_name}.py")
    
    # Check for case sensitivity (especially on Linux/Railway)
    if not os.path.exists(script_path):
        lower_path = os.path.join(scripts_dir, f"{script_name.lower()}.py")
        if os.path.exists(lower_path):
            script_path = lower_path
        else:
            available = [f.replace(".py", "") for f in os.listdir(scripts_dir) if f.endswith(".py")]
            return f"❌ Erro: O script '{script_name}.py' não foi encontrado.\n\nScripts disponíveis: {', '.join(available)}"
    
    try:
        # Use the same python interpreter running the bot
        cmd = [sys.executable, script_path] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30 # Safety timeout
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"⚠️ Erro na execução:\n{result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "🛑 Erro: O script demorou muito para responder (timeout de 30s)."
    except Exception as e:
        return f"🔥 Erro interno ao rodar o script: {str(e)}"
