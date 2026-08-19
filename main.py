client_name= input("Enter client name:")
client_email=input("Enter client email:")
while True:    
      try:
          budget=int(input("Enter budget:"))
          break
      except ValueError:
            print("Please enter a valid budget:")
while True:
    appointment_booked = input("Appointment booked?(yes/no)").lower()
    if appointment_booked in ["yes", "no"]:
        break
    print("Please enter yes or no.")
appointment_booked= appointment_booked =="yes"
while True:
    interested = input("Are you interested on our service?(yes/no)").lower()
    if interested in ["yes", "no"]:
        break
    print("Please enter yes or no.")
interested= interested =="yes"
from lead import Lead
lead1=Lead(client_name,client_email,budget,appointment_booked,interested)
lead1.qualify()
