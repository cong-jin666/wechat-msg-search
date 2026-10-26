from tkinter import *
from tkinter import messagebox, filedialog

# 登录微信
def login_wechat():
    messagebox.showinfo("登录", "微信登录功能尚未实现。")

# 导出聊天记录
def export_records():
    messagebox.showinfo("导出", "聊天记录导出功能尚未实现。")

# AI 分析
def ai_analysis():
    messagebox.showinfo("AI分析", "AI分析功能尚未实现。")

# 文本查找
def text_search():
    messagebox.showinfo("文本查找", "文本查找功能尚未实现。")

# 图片查找
def image_search():
    messagebox.showinfo("图片查找", "图片查找功能尚未实现。")

# 切换界面函数
def showAccount():
    libraryFrame.pack_forget()
    AIFrame.pack_forget()
    searchFrame.pack_forget()
    accountFrame.pack(expand=True)

def showLibrary():
    accountFrame.pack_forget()
    AIFrame.pack_forget()
    searchFrame.pack_forget()
    libraryFrame.pack(expand=True)

def showAI():
    accountFrame.pack_forget()
    libraryFrame.pack_forget()
    searchFrame.pack_forget()
    AIFrame.pack(expand=True)

def showSearch():
    accountFrame.pack_forget()
    libraryFrame.pack_forget()
    AIFrame.pack_forget()
    searchFrame.pack(expand=True)

# 主窗口设置
root = Tk()
root.title("微信助手 Ver0.1")
root.geometry("600x400")
root.resizable(False, False)

# 设置背景颜色
root.configure(bg="#f5f5f5")

# 居中显示窗口
window_width = 600
window_height = 400
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_coordinate = int((screen_width / 2) - (window_width / 2))
y_coordinate = int((screen_height / 2) - (window_height / 2))
root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

# 侧边按钮
sideColumnFrame = Frame(root, bg="#ffffff", bd=2, relief="groove")
sideColumnFrame.pack(side="left", fill="y", padx=10, pady=10)

Button(sideColumnFrame, text="账号信息", command=showAccount, font=("Arial", 12), padx=10, pady=10, bg="#4CAF50", fg="white").pack(fill="x", pady=5)
Button(sideColumnFrame, text="记录导出", command=showLibrary, font=("Arial", 12), padx=10, pady=10, bg="#2196F3", fg="white").pack(fill="x", pady=5)
Button(sideColumnFrame, text="AI分析", command=showAI, font=("Arial", 12), padx=10, pady=10, bg="#FF9800", fg="white").pack(fill="x", pady=5)
Button(sideColumnFrame, text="查找功能", command=showSearch, font=("Arial", 12), padx=10, pady=10, bg="#9C27B0", fg="white").pack(fill="x", pady=5)

# 账号信息界面
accountFrame = Frame(root, bg="#f5f5f5")
accountFrame.pack(expand=True)

Label(accountFrame, text="当前已登录用户：", font=("Arial", 14), bg="#f5f5f5").pack(pady=10)
Button(accountFrame, text="登录微信", command=login_wechat, font=("Arial", 12), padx=10, pady=10, bg="#4CAF50", fg="white").pack(pady=5)
Button(accountFrame, text="退出登录", command=lambda: messagebox.showinfo("退出", "退出登录功能尚未实现。"), font=("Arial", 12), padx=10, pady=10, bg="#F44336", fg="white").pack(pady=5)

# 聊天记录导出界面
libraryFrame = Frame(root, bg="#f5f5f5")
Button(libraryFrame, text="聊天记录导出", command=export_records, font=("Arial", 12), padx=10, pady=10, bg="#2196F3", fg="white").pack(pady=10)

# AI 分析界面
AIFrame = Frame(root, bg="#f5f5f5")
Button(AIFrame, text="AI分析", command=ai_analysis, font=("Arial", 12), padx=10, pady=10, bg="#FF9800", fg="white").pack(pady=10)

# 查找功能界面
searchFrame = Frame(root, bg="#f5f5f5")

Label(searchFrame, text="文本查找:", font=("Arial", 12), bg="#f5f5f5").pack(pady=5)
text_entry = Entry(searchFrame, font=("Arial", 12))
text_entry.pack(pady=5)
Button(searchFrame, text="查找", command=text_search, font=("Arial", 12), padx=10, pady=5, bg="#4CAF50", fg="white").pack(pady=5)

Label(searchFrame, text="图片查找:", font=("Arial", 12), bg="#f5f5f5").pack(pady=10)
Button(searchFrame, text="图片查找", command=image_search, font=("Arial", 12), padx=10, pady=5, bg="#2196F3", fg="white").pack(pady=5)

# 启动主循环
root.mainloop()
