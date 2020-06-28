# 自定义过滤器实现格式转换

def func_index_convert(value):

    # if value == 1:
    #     return "first"
    # elif value == 2:
    #     return "second"
    # elif value == 3:
    #     return "third"
    # else:
    #     return ""
    # 上面这种方式可以实现,下面用另一种方法
    index_dict = {1:"first",
                  2:"second",
                  3:"third"
                  }
    return index_dict.get(value,"")