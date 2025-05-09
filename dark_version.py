import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QHBoxLayout, QTextEdit, QFrame, QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QIcon
import yt_dlp
import qdarkstyle


class DownloadWorker(QObject):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    open_signal = pyqtSignal(str)

    def __init__(self, url, folder):
        super().__init__()
        self.url = url
        self.folder = folder

    def run(self):
        self.status_signal.emit("开始下载...")
        self.log_signal.emit("开始下载: " + self.url)

        ffmpeg_installed = shutil.which("ffmpeg") is not None
        if ffmpeg_installed:
            self.log_signal.emit("✅ 已检测到 ffmpeg，启用分离流下载...")
            ydl_format = 'bestvideo+bestaudio/best'
            merge_format = 'mp4'
            postprocessors = [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': merge_format},
                {'key': 'FFmpegEmbedSubtitle'},
                {'key': 'FFmpegMetadata'},
            ]
        else:
            self.log_signal.emit("⚠️ 未检测到 ffmpeg，使用兼容模式...")
            ydl_format = 'best[ext=mp4]'
            postprocessors = []
            merge_format = None

        ydl_opts = {
            'format': ydl_format,
            'outtmpl': os.path.join(self.folder, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'progress_hooks': [self.yt_hook],
            'logger': self.YTDLogger(self),
            'postprocessors': postprocessors,
            'merge_output_format': merge_format,
            'prefer_ffmpeg': True,
            'postprocessor_args': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.progress_signal.emit(100)
            self.status_signal.emit("下载完成！")
            self.log_signal.emit("下载成功！")
            self.open_signal.emit(self.folder)
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

    def yt_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percent = int(downloaded * 100 / total) if total else 0
            self.progress_signal.emit(percent)
            self.status_signal.emit(f"下载中：{percent}%")
        elif d['status'] == 'finished':
            self.status_signal.emit("合并音视频中...")
            self.log_signal.emit("合并音视频中...")

    class YTDLogger:
        def __init__(self, outer):
            self.outer = outer

        def debug(self, msg):
            self.outer.log_signal.emit(msg)

        def warning(self, msg):
            self.outer.log_signal.emit("警告：" + msg)

        def error(self, msg):
            self.outer.log_signal.emit("错误：" + msg)


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube 高清下载器 📹")
        self.setWindowIcon(QIcon("ico.ico"))  

        self.setFixedSize(1200, 900)

        # 主布局
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignCenter)

        # 卡片样式容器
        frame = QFrame()
        frame.setFixedSize(1050, 830)
        frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 20px;
                padding: 10px;
            }
        """)
        # 全局样式美化
        self.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 500;
            }

            QLineEdit {
                font-size: 18px;
                padding: 6px 12px;
                border-radius: 5px;
                border: 1.5px solid #555555;;
                background-color: #3c3f41;
                color: #ffffff;
            }

          QPushButton {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29,
                    stop:0.5 #302b63,
                    stop:1 #24243e
                );
                color: #ffffff;
                border: 1px solid #00ffe0;
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 1px;
                }
            
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00c6ff,
                    stop:1 #0072ff
                );
                border: 1px solid #00ffae;
                color: #ffffff;
            }
            
            QPushButton:pressed {
                background-color: #00ffe0;
                color: #000000;
                border: 1px solid #00ffe0;
            }


           QProgressBar {
                border: 1px solid #00ffe0;
                border-radius: 10px;
                background-color: #1e1e1e;
                text-align: center;
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
            }
            
            QProgressBar::chunk {
                background: QLinearGradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #00f0ff,
                    stop: 0.5 #00c0ff,
                    stop: 1 #0077ff
                );
                border-radius: 8px;
                margin: 1px;
            }
            
            QTextEdit {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #0f2027,
                stop:0.5 #203a43,
                stop:1 #2c5364
            );
            font-size: 20px;
            color: #00ffe0;
            border-radius: 12px;
            padding: 10px;
            border: 1px solid #00fff7;
            font-family: "Consolas", "Courier New", monospace;
        }

        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        title = QLabel("🎬 YouTube 高清下载器")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #32Aaff;")
        layout.addWidget(title)

        # 输入部分
        self.url_label = QLabel("视频链接：")
        self.url_input = QLineEdit()

        self.folder_label = QLabel("保存目录：")
        folder_layout = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_button = QPushButton("📁 选择目录")
        self.folder_button.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(self.folder_button)

        # 状态与按钮
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFixedHeight(35)
        self.status_label = QLabel("准备就绪")
        self.download_button = QPushButton("⬇️ 开始下载")
        self.download_button.clicked.connect(self.download_video)

        # 日志框
        self.output_label = QLabel("下载日志：")
        self.output_box = QTextEdit()
        self.output_box.setMaximumHeight(280)
        self.output_box.setReadOnly(True)

        # 添加到布局
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.folder_label)
        layout.addLayout(folder_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.download_button)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_box)

        frame.setLayout(layout)
        outer_layout.addWidget(frame)

        self.setLayout(outer_layout)

        # 线程设置
        self.worker = None
        self.worker_thread = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if folder:
            self.folder_path.setText(folder)

    def download_video(self):
        url = self.url_input.text().strip()
        folder = self.folder_path.text().strip()

        if not url or not folder:
            QMessageBox.warning(self, "错误", "请填写链接并选择保存目录")
            return

        self.progress_bar.setValue(0)
        self.output_box.clear()

        self.worker = DownloadWorker(url, folder)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.thread_cleanup)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.open_signal.connect(self.open_folder)

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def thread_cleanup(self):
        self.status_label.setText("完成！")
        self.worker_thread.quit()
        self.worker_thread.wait()

    def handle_error(self, msg):
        self.status_label.setText("下载失败")
        self.append_log("错误：" + msg)
        QMessageBox.critical(self, "下载失败", msg)
        self.worker_thread.quit()
        self.worker_thread.wait()

    def open_folder(self, path):
        try:
            os.startfile(path)
        except Exception as e:
            self.append_log(f"无法打开目录: {str(e)}")

    def append_log(self, message):
        self.output_box.append(message)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())

