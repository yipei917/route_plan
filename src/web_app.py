from flask import Flask, render_template, jsonify
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
from src.utils.scheduler import Scheduler
import time
import os

# 设置模板目录路径
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

# 全局调度器
scheduler = None
step_count = 0

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/start')
def start_simulation():
    """开始模拟"""
    global scheduler, step_count
    scheduler = Scheduler(num_vehicles=2, step_size=3)
    scheduler.initialize()
    step_count = 0
    return jsonify({'status': 'success', 'message': '模拟已开始'})

@app.route('/next')
def next_step():
    """执行下一步"""
    global scheduler, step_count
    if scheduler is None:
        return jsonify({'status': 'error', 'message': '请先开始模拟'})
    
    try:
        step_count += 1
        
        # 执行一步模拟
        scheduler.assign_task()
        if not scheduler.simulator.simulate_step():
            return jsonify({'status': 'finished', 'message': '所有任务已完成'})
        scheduler.check_status()
        
        # 直接生成图像数据，不保存文件
        scheduler.grid_visualizer.draw_grid()
        scheduler.grid_visualizer.draw_vehicles()
        img_data = scheduler.grid_visualizer.get_image_data()
        
        return jsonify({
            'status': 'success', 
            'image': img_data,
            'step': step_count,
            'message': f'第{step_count}步执行完成'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'执行出错: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True) 