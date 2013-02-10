int btnInt = 8;
int btnExt = 9;
int relay  = 11;
int led    = 12;

char msg = ' ';

boolean override = false;
boolean error    = false;
boolean errorLED = false;

void setup() {
  pinMode(btnInt, INPUT);
  pinMode(btnExt, INPUT);
  pinMode(relay,  OUTPUT);
  pinMode(led,    OUTPUT);
  
  Serial.begin(9600);
  
  // Default to open
  digitalWrite(relay, HIGH);
}

void loop() {
  while (Serial.available()>0){
    msg = Serial.read();
  }
  
  if (msg == 'P') {
    digitalWrite(relay, LOW);
    msg = ' ';
  }
  
  if (msg == 'R') {
    digitalWrite(relay, HIGH);
    msg = ' ';
  }
  
  if (msg == 'E') {
    msg = ' ';
    if (!override) {
      error = true;
    } else {
      digitalWrite(relay, HIGH);
    }
  }
  
  if (digitalRead(btnExt) == HIGH) {
     Serial.println("T");
     delay(500);
  }
  
  if (digitalRead(btnInt) == HIGH) {
    override = !override;
    error = false;
    if (override) {
      digitalWrite(relay, HIGH);
      digitalWrite(led, HIGH);
    } else {
      digitalWrite(led, LOW);
    }
    delay(500);
  }
  
  if (error) {
    errorLED = !errorLED;
    digitalWrite(led, errorLED ? HIGH : LOW);
    delay(100);
  }
}
