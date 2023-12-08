import time
from tkinter import *
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageTk
import worker
import schedule
from tkinter import ttk

# 创建一个Tkinter窗口实例
win = Tk()

win.title("小德同步工具")
# 设置窗口的大小
win.geometry("800x800")
win.resizable(0, 0)
win.columnconfigure(0, weight=1)

# constants
LOCAL_JSON_DB = 'settings.json'
wx_infos = []

msg = StringVar()
cur_user = StringVar()
last_sync_time = StringVar()
sync_period = StringVar()

treeview = ttk.Treeview(win, columns=('c1', 'c2', 'c3', 'c4', 'c5'), show="headings")
# 设置每列宽度和对齐方式
treeview.column('c1', width=120, anchor='center')
treeview.column('c2', width=100, anchor='center')
treeview.column('c3', width=100, anchor='center')
treeview.column('c4', width=100, anchor='center')
treeview.column('c5', width=120, anchor='center')
# 设置每列表头标题文本
treeview.heading('c1', text='微信昵称')
treeview.heading('c2', text='微信号')
treeview.heading('c3', text='手机号')
treeview.heading('c4', text='WxID')
treeview.heading('c5', text='是否同步')

def resetAll():
    msg.set('')
    cur_user.set('')
    last_sync_time.set('')
    sync_period.set('')


def checkAgain():
    global wx_infos
    resetAll()

    wx_infos = worker.get_info()
    if wx_infos is None:
        msg.set('请先登录微信，然后重新检测')
    else:
        for wx in wx_infos:
            wx['allow_sync'] = True

            # 如获取不到account，尝试用wxid赋值，不一定能破解成功
            if wx['account'] == 'None':
                wx['account'] = wx['wxid']

            treeview.insert('', 'end', values=(wx['name'], wx['account'], wx['mobile'], wx['wxid'], '☑'), tags='checkbox')

    sync_period.set('定时上传时间：每天14:10')


def do_sync_by_schedule():
    print('定时任务触发，开始同步任务...')
    # checkAgain()
    # if wx_infos is None:
    #     return

    do_sync()


def do_sync():
    global wx_infos
    children = treeview.get_children()
    if not children or len(children) == 0:
        print('当前没有需要同步的任务执行...')
        return

    allow_wxs = list(filter(lambda x: x['allow_sync'] == True, wx_infos))
    if not allow_wxs:
        print('当前没有需要同步的任务执行...')
        return

    print(f'需要同步 {len(allow_wxs)} 个微信账号的数据')
    print(allow_wxs)

    for idx, wx_info in enumerate(allow_wxs):
        print(f'开始同步：{idx + 1}/{len(allow_wxs)}')
        ret = worker.exec_sync(wx_info)
        if not ret:
            print(f'第{idx + 1}个微信同步失败')



lbl_msg = Label(win, textvariable=msg, fg='red')
lbl_user = Label(win, textvariable=cur_user)
lbl_last_sync_time = Label(win, textvariable=last_sync_time)
lbl_sync_period = Label(win, textvariable=sync_period)
# 重新检测按钮
btn_check = Button(win, text="重新检测", command=checkAgain)
btn_sync = Button(win, text="立即同步", command=do_sync)

treeview.grid(row=6, column=0)


lbl_msg.grid(row=0, column=0, pady=(10, 10), padx=(10, 10))
lbl_user.grid(row=1, column=0, pady=(10, 10), padx=(10, 10))
lbl_last_sync_time.grid(row=2, column=0, pady=(10, 10))
lbl_sync_period.grid(row=3, column=0, pady=(10, 10))
btn_check.grid(row=4, column=0, pady=(10, 10))
btn_sync.grid(row=5, column=0, pady=(10, 10))



# 定义复选框回调函数
def checkbutton_callback(event):
    global wx_infos
    # 获取选中项
    selected_item = treeview.selection()[0]
    if not selected_item:
        return

    vals = treeview.item(selected_item, 'values')
    # 获取复选框状态
    checked = vals[4]
    # 更新复选框状态
    if checked == '☐':
        treeview.set(selected_item, '#5', '☑')
        # treeview.set(selected_item, 'c4', ('1',))
    else:
        treeview.set(selected_item, '#5', '☐')
        # treeview.set(selected_item, 'c4', ('0',))
    for wx in wx_infos:
        if wx['wxid'] == vals[3]:
            wx['allow_sync'] = True if checked == '☐' else False

# 插入复选框
treeview.tag_configure('checkbox', font=('TkDefaultFont', 12))
treeview.tag_bind('checkbox', '<ButtonRelease-1>', checkbutton_callback)
# for item1 in treeview.get_children():
#     treeview.set(item1, 'c4', '☐')
#     # treeview.tag_bind(item1, '<ButtonRelease-1>', lambda event, item=item1: checkbutton_callback())
#     treeview.item(item1, tags=('checkbox',))

# call once on run
checkAgain()

# 增加定时任务同步数据
schedule.every().day.at("14:10").do(do_sync_by_schedule)


# 为退出窗口定义一个函数
def quit_window(icon, item):
    icon.stop()
    win.destroy()


# 定义一个函数以再次显示窗口
def show_window(icon, item):
    win.deiconify()

    # icon.stop()
    # win.after(0,win.deiconify())


# 隐藏窗口并在系统任务栏上显示
def hide_window():
    win.withdraw()
    image = Image.open("favicon.ico")
    menu = (item('显示', show_window), item('退出', quit_window))
    icon = pystray.Icon("name", image, "力德数据同步", menu)
    icon.run()


win.protocol('WM_DELETE_WINDOW', hide_window)

win.mainloop()

while True:
    schedule.run_pending()
    time.sleep(1)
