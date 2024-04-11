from numpy import angle

class SignalProcessing:
    @staticmethod
    def process_gas_phase(s21_batch):
        # Calculates and reurns the phase of the S21 parameters. 
        return angle(s21_batch)
    
    @staticmethod
    def process_direction(s11_batch, s21_batch):
        return s11_batch + s21_batch

