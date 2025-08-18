# Aid.Scripts

申必脚本库。**由AI申必力量驱动。**

## lyrics_process.py

处理HyPlayer保存的歌词文件。

自动扫描整个文件夹中的lrc歌词。

处理前：

```
[time] lyrics  「歌词翻译」
...
```

处理后：

```
[time] lyrics
...
[time] 歌词翻译
```

目前在Salt Player上可以正常使用。


## matlab_data_viewer.py

使用Tkinter将MATLAB数据文件(.mat)读取并进行可视化的小工具，支持多通道叠加。

## tieba_client_sign.py

百度贴吧HTTP Request的Sign值计算器。

## tracker.py

记录实验数据到CSV文件。