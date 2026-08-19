class Lead:

    def __init__(self, name, email, budget, appointment_booked, interested):
        self.name = name
        self.email = email
        self.budget = budget
        self.appointment_booked = appointment_booked
        self.interested = interested

    def qualify(self):
        qualified = True
        reasons = []

        if self.budget < 100000:
            qualified = False
            reasons.append("Your budget should be at least 100,000.")

        if not self.appointment_booked:
            qualified = False
            reasons.append("You should book an appointment.")

        if not self.interested:
            qualified = False
            reasons.append("You should be interested in our service.")

        if qualified:
            return "Qualified Lead", reasons
        else:
            return "Not Qualified", reasons