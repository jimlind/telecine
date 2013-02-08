int relay = 8;
int btnB  = 10;
int led   = 12;
int board = 13;
char msg = ' ';

boolean override = false;
boolean error    = false;
boolean errorLED = false;

void setup() {
  pinMode(relay, OUTPUT);
  pinMode(led,   OUTPUT);
  pinMode(board, OUTPUT);
  
  pinMode(btnB,  INPUT);
  
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
  
  if (digitalRead(btnB) == HIGH) {
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
