
#compute 2^100
#x=1
#for i in range(0,3):
#    x = x * 2
#print(x)

#compute 1*2*3*...*10
#x=1
#for i in range(1,11):
#    x=i*x
#    print (x)

loan = int(input("Enter the loan amount: "))
interest = int(input("Enter interest amount: "))



while( (x > 100) || (x < 0) )
    #do something



valid = False

if interest > 100:
    print("invalid interest")
    interest = int(input("Enter interest amount: "))
    

payments = int(input("Enter number of payments: "))

monthly = (loan + (loan * 0.01 * interest))/payments

print("Your monthly payments are ", monthly)
