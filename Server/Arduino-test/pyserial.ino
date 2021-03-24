int fieldIndex = 0;
char message[30];
char ch;

void setup() {
	Serial.begin(9600);
}

void loop() {

	if (Serial.available()) {
		ch = Serial.read();
		if (ch == 10) {
			message[fieldIndex] = 0;
			if (message[0] == '>') { // comandi
				if (message[1] == 'C') {
					Serial.println("C4b7caa5d-2634-44f3-ad62-5ffb1e08d73f");
				}
				else {
					Serial.println(message);
				}
			}
			else { // aggiornamenti
				Serial.println(message);
			}
			message[0] = 0; // ready to start over
			fieldIndex = 0;
		}
		else {
			message[fieldIndex] = ch;
			fieldIndex++;
		}
	}
}
