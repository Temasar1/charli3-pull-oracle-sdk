from pycardano import Address

addr_str = "addr_test1qr6784s76cawztg7t7en4f79wfrf474zdyhkr5k07sv7uzdg6ske4tqzye89y4g46ht4wh7gruqpcldl942r0ned3flsgl7q4t"
addr = Address.from_primitive(addr_str)

print(f"Address: {addr_str}")
print(f"Payment part type: {type(addr.payment_part)}")
print(f"Payment part hex: {addr.payment_part.to_primitive().hex()}")
