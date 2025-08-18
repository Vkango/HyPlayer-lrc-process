from urllib.parse import unquote
from urllib.parse import quote
import hashlib
def CalcSign(Original_Data):#计算sign
    text = Original_Data
    proceed = unquote(text)
    proceed = proceed.replace("&", "", -1) + "tiebaclient!!!"
    proceed = hashlib.md5(proceed.encode()).hexdigest()
    return text + "&sign=" + proceed.upper()