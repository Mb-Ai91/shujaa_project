from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/shujaa-task', methods=['POST'])
def handle_task():
    # استقبال الأمر القادم من الواجهة
    data = request.json or {}
    topic = data.get("command", "تحليل عام")

    # كود تشغيل الوكلاء وتمرير الأمر لهم بسلاسة في الخلفية
    cmd = f'cd /workspaces/shujaa_project/shujaa_crew && source .venv/bin/activate && export TERM=dumb && (echo "{topic}" | uv run crewai run > n8n_output.log 2>&1)'

    # تشغيل المهمة دون تعطيل النظام
    subprocess.Popen(cmd, shell=True)

    # إرسال تأكيد فوري بالاستلام
    return jsonify({
        "status": "success",
        "message": f"المدير شجاع: تم استلام الأمر ({topic}) وتوجيه الوكلاء للعمل في الخلفية!"
    })

if __name__ == '__main__':
    # تشغيل الخادم على المنفذ 5000
    app.run(host='0.0.0.0', port=5000)
