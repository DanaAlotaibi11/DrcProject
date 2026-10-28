import serial
import numpy as np
import features

PORT= "COM3"
BAUD_RATE=115200
WINDOW_SIZE=1000
SAMPLE_RATE=1000 #Hz

def main():
    print("Connecting to COM3")
    arduino=serial.Serial(PORT,BAUD_RATE,timeout=1)

    mic1_buf, mic2_buf, vib_buf= [],[],[] #empty lists for the mic1, mic2, and piezo
    print("Listening...")
    try:
        while true:
            raw=arduino.readline().decode('utf-8').strip() #reads serial output of our esp code
            if not raw:
                continue
            try: #format: mic1,mic2,piezo || this reads esp readings and puts it into the lists we made
                m1,m2,vib=raw.split(',')
                mic1_buf.append(float(m1))
                mic2_buf.append(float(m2))
                vib_buf.append(float(vib))
            except ValueError: #ignores corrupted lines(check)
                continue
            if len(mic1_buf)>=WINDOW_SIZE:# does it fit our array size? yes then put it into np arrays
                m1_array=np.array(mic1_buf)
                m2_array=np.array(mic2_buf)
                vib_array=np.array(vib_buf)

                #now pass it to the engine via extract function
                results=features.extract_features(mic1=m1_array,
                                                  mic2=m2_array,
                                                  vibration=vib_array,
                                                  fs=SAMPLE_RATE,
                                                  include_spectrum=False)
                print(f"Mic1 RMS: {results['mic1']['rms']:.2f} | Vibration Peak: {results['vibration']['max_peak']:.2f}")
                mic1_buf.clear()
                mic2_buf.clear()
                vib_buf.clear() #clears buffers before reading again
    except KeyboardInterrupt:
        print("\nStopping data collection")
    finally:
        arduino.close()
if __name__=="__main__":
    main()



