import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import os
import threading
from PIL import Image, ImageTk

class VideoFrameExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频帧提取与播放工具")
        self.root.geometry("640x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # 设置 ttk 主题
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#4a90e2", foreground="white")
        style.map("TButton", background=[("active", "#357ABD")])
        style.configure("TProgressbar", thickness=20, troughcolor="#e0e0e0", background="#4caf50")
        style.configure("TLabel", background="#f0f0f0", foreground="black")

        # UI Elements
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill="both", expand=True)

        self.select_button = ttk.Button(main_frame, text="选择视频文件", command=self.select_video_file)
        self.select_button.pack(pady=10, fill='x')

        # 视频预览区域
        video_container = ttk.LabelFrame(main_frame, text="视频预览", padding=5)
        video_container.pack(pady=10)

        self.video_frame = tk.Label(video_container, bg="black", width=640, height=360)
        default_image = Image.new('RGB', (640, 360), color='white')
        default_image_tk = ImageTk.PhotoImage(default_image)
        self.video_frame.config(image=default_image_tk)
        self.video_frame.image = default_image_tk
        self.video_frame.pack()

        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=10)

        self.play_button = ttk.Button(control_frame, text="暂停", command=self.toggle_play, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5, expand=True, fill='x')

        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_playback, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, expand=True, fill='x')

        # 进度条和状态标签
        self.progress_bar = ttk.Progressbar(
            main_frame, orient='horizontal', length=300, mode='determinate', style="TProgressbar"
        )
        self.progress_bar.pack(pady=10)

        self.status_label = ttk.Label(main_frame, text="等待用户操作...", foreground="blue", font=("微软雅黑", 10))
        self.status_label.pack(pady=5)

        # 播放控制变量
        self.cap = None
        self.is_playing = False
        self.is_paused = False
        self.current_frame = None
        self.output_dir = None
        self.frame_count = 0
        self.total_frames = 0

    def select_video_file(self):
        video_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv")]
        )
        if not video_path:
            return
        self.process_and_play_video(video_path)

    def process_and_play_video(self, video_path):
        self.output_dir = os.path.join(os.path.dirname(video_path),
                                       f"{os.path.splitext(os.path.basename(video_path))[0]}_frames")
        os.makedirs(self.output_dir, exist_ok=True)

        self.cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
        if not self.cap.isOpened():
            messagebox.showerror("错误", "无法打开视频文件")
            return

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_count = 0
        self.is_playing = True
        self.is_paused = False
        self.play_button.config(text="暂停", state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.config(maximum=self.total_frames)

        threading.Thread(target=self.play_loop, daemon=True).start()

    def play_loop(self):
        while self.is_playing and self.cap.isOpened():
            if not self.is_paused:
                ret, frame = self.cap.read()
                if not ret:
                    self.root.after(0, self.stop_playback)
                    break

                resized = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
                img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img)
                img_tk = ImageTk.PhotoImage(img_pil)

                self.current_frame = img_tk
                self.root.after(0, self.update_video_label, img_tk)

                output_path = os.path.join(self.output_dir, f"frame_{self.frame_count:04d}.jpg")
                success, encoded_image = cv2.imencode('.jpg', frame)
                if success:
                    with open(output_path, 'wb') as f:
                        f.write(encoded_image.tobytes())
                    self.frame_count += 1
                    self.root.after(0, self.progress_bar.config, {"value": self.frame_count})
                    self.root.after(0, self.status_label.config,
                                    {"text": f"已提取 {self.frame_count}/{self.total_frames} 帧"})

                cv2.waitKey(40)
            else:
                cv2.waitKey(100)

    def update_video_label(self, img_tk):
        self.video_frame.config(image=img_tk)
        self.video_frame.image = img_tk

    def toggle_play(self):
        self.is_paused = not self.is_paused
        self.play_button.config(text="继续" if self.is_paused else "暂停")

    def stop_playback(self):
        self.is_playing = False
        self.is_paused = False
        self.cap.release()
        self.play_button.config(text="暂停", state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.config(value=0)
        self.status_label.config(text="处理完成！", fg="green")
        self.video_frame.config(image=None)
        self.video_frame.image = None
        messagebox.showinfo("完成", "视频帧已成功提取！")


if __name__ == "__main__":
    try:
        import pyi_splash
        pyi_splash.update_text("加载中...")  # 可选：更新文字
        pyi_splash.close()
    except ImportError:
        pass

    root = tk.Tk()
    app = VideoFrameExtractorApp(root)
    root.mainloop()
