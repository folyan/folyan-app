import random

popa=("камень","ножницы","бумага")
botik=random.choice(popa)
coolmon=input("камень,ножницы или бумага?").lower().strip()

while coolmon not in popa:
 print("Хуйню не пиши")
 coolmon=input("Еще раз сучара!").lower().strip()

contra={
"камень":"ножницы",
"ножницы":"бумага",
"бумага":"камень"}

if coolmon==botik:print("Ничья!")
elif contra[coolmon]==botik:print("Победа!")
else:print(f"Мы вьебали эту игру!Ответ ботика:{botik}")