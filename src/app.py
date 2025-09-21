from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from ai_service import AIService
from insight import Insight

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize services
ai_service = AIService()
insight = Insight()

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('chat.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and provide AI responses with cluster context"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        namespace = data.get('namespace', 'code-analyzer')
        conversation_history = data.get('history', [])  # Array of previous messages
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get current cluster context
        cluster_context = insight.get_cluster_context(namespace)
        
        # Build conversation context if history exists
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-4:]:  # Keep last 4 messages for context
                role = "User" if msg.get('role') == 'user' else "Assistant"
                conversation_context += f"{role}: {msg.get('content', '')}\n"
        
        # Create a comprehensive prompt for the AI
        system_context = f"""
You are a Kubernetes cluster expert assistant. You have access to real-time cluster information.

Current Cluster Context (Namespace: {namespace}):
{json.dumps(cluster_context, indent=2)}

Based on this cluster information, answer the user's question. Provide specific details about:
- Pod status and health
- Resource usage and capacity
- Configuration issues
- Deployment status
- Storage and networking
- Recent events and problems

If the user asks about cluster health, analyze the data and provide insights.
Be specific and reference actual resource names and values from the context.{conversation_context}
"""
        
        full_prompt = f"{system_context}\n\nUser Question: {user_message}\n\nAnswer:"
        
        # Get AI response
        ai_response = ai_service.generate_text(full_prompt, max_tokens=1500)
        
        print(f"AI Response: {ai_response}")
        return jsonify({
            'response': ai_response,
            'cluster_context': cluster_context,
            'namespace': namespace
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cluster-status', methods=['GET'])
def cluster_status():
    """Get current cluster status"""
    try:
        namespace = request.args.get('namespace', 'code-analyzer')
        context = insight.get_cluster_context(namespace)
        print(context)
        return jsonify(context)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health-check', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Kubernetes Insights AI Chat'})

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)