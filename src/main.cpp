#include "DHT20.h"
#include <TFT_eSPI.h> // Graphics and font library for ILI9341 driver chip
#include <WiFi.h>
#include <HttpClient.h>
#include <IPAddress.h>
#include <SoftWire.h>

#define uS_TO_S_FACTOR 1000000ULL /* Conversion factor for micro seconds to seconds */
#define TIME_TO_SLEEP  3600          /* Time ESP32 will go to sleep (in seconds) */

#define SW_SCL 13
#define SW_SDA 15

#define DEBUG false

// I2C address of DHT20
const uint8_t DHT20_ADDRESS = 0x38;

SoftWire sw(SW_SDA, SW_SCL);
// These buffers must be at least as large as the largest read or write you perform.
char swTxBuffer[16];
char swRxBuffer[16];

TFT_eSPI tft = TFT_eSPI();  // Invoke library, pins defined in User_Setup.h

DHT20 outsideDHT;

uint8_t count = 0;

char ssid[] = "";     
//char ssid[] = "";
char pass[] = ""; 
const char kHostname[] = "";

// SW DHT I2C VARS

float    _humidity;
float    _temperature;
float    _humOffset;
float    _tempOffset;

uint8_t  _status;
uint32_t _lastRequest;
uint32_t _lastRead;
uint8_t  _bits[7];

// FUNCS

inline float toFahrenheit(float C);
void print_DHT20_error(int status);
bool SW_DHT20_begin();
bool SW_DHT20_isConnected();
bool isMeasuring();
int SW_DHT20_read();
uint8_t SW_DHT20_readStatus();
uint8_t SW_DHT20_resetSensor();
int SW_DHT20_requestData();
int SW_DHT20_readData();
int SW_DHT20_convert();
uint8_t _crc8(uint8_t *ptr, uint8_t len);
bool SW_DHT20_resetRegister(uint8_t reg);


void print_wakeup_reason();

void setup()
{
  Serial.begin(9600);

  print_wakeup_reason();

  Serial.println(__FILE__);
  Serial.print("DHT20 LIBRARY VERSION: ");
  Serial.println(DHT20_LIB_VERSION);
  Serial.println();

  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);

  // HW i2c begin
  Wire.begin();

  // SW i2c begin
  sw.setTxBuffer(swTxBuffer, sizeof(swTxBuffer));
  sw.setRxBuffer(swRxBuffer, sizeof(swRxBuffer));
  sw.setDelay_us(5);
  sw.setTimeout(1000);
  sw.begin();

  // drivers begin
  outsideDHT.begin();    //  ESP32 default pins 21 22
  int insideStatus = SW_DHT20_begin();
  while (!insideStatus) {
    Serial.print("sw spi? ");
    Serial.println(insideStatus);
    delay(2000);
    insideStatus = SW_DHT20_begin();
  }
  
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("MAC address: ");
  Serial.println(WiFi.macAddress());

  tft.drawString("WiFi Connected", 0, 0);


  delay(1000);
}


void loop()
{
    //  READ DATA
    uint32_t start = micros();
    int status = outsideDHT.read();
    int statusINSIDE = SW_DHT20_read();
    uint32_t stop = micros();

    if ((count % 10) == 0)
    {
      count = 0;
      Serial.println();
      Serial.println("Type\tHumidity (%)\tTemp (°C)\tIN Hum\t In TEMP\t Time (µs)\tStatus");
    }
    count++;

    print_DHT20_error(status);
    print_DHT20_error(statusINSIDE);
  


    char display_buff [50];
    sprintf(display_buff, "Outside Temperature: %f", outsideDHT.getTemperature());
    tft.drawString(display_buff, 0, 0);
    sprintf(display_buff, "Outside Humidity: %f", outsideDHT.getHumidity());
    tft.drawString(display_buff, 0, 15);

    sprintf(display_buff, "Inside Temperature: %f", _temperature);
    tft.drawString(display_buff, 0, 30);
    sprintf(display_buff, "Inside Humidity: %f", _humidity);
    tft.drawString(display_buff, 0, 45);

    
    if (status || !outsideDHT.getTemperature() || !outsideDHT.getHumidity() || !_temperature || !_humidity) {
      delay(2000);
      return loop(); // tail end recursion to save memory on continous sensor issue
    }

    int err = 0;
  
    WiFiClient c;
    HttpClient http(c);

    char buffer [80];
    snprintf(buffer, 80, "/Live/data?temp=%.4f&hum=%.4f&itemp=%.4f&ihum=%.4f", toFahrenheit(outsideDHT.getTemperature()), outsideDHT.getHumidity(), toFahrenheit(_temperature), _humidity);
  
#if !DEBUG // only post when not in debug mode
    err = http.post(kHostname, 80, buffer); 
    http.stop();
#endif
    Serial.print("DHT20 \t");
    //  DISPLAY DATA, sensor has only one decimal.
    Serial.print(outsideDHT.getHumidity(), 1);
    Serial.print("\t\t");
    Serial.print(outsideDHT.getTemperature(), 1);
    Serial.print("\t\t");
    Serial.print(_humidity, 1);
    Serial.print("\t\t");
    Serial.print(_temperature, 1);
    Serial.print("\t\t");
    Serial.print(stop - start);
    Serial.print("\t\t");
    

  

  uint64_t sleep = 15 * 60 * 1000 * 1000;

  Serial.println("Going to sleep");

  delay(2000);

#if DEBUG
  return; // if in debug mode, lets not sleep.
#endif

  esp_sleep_enable_timer_wakeup(sleep);
  esp_deep_sleep_start();

  
}

inline float toFahrenheit(float C) {
  return 1.8 * C + 32.0;
}

//Function that prints the reason by which ESP32 has been awaken from sleep
void print_wakeup_reason(){
  esp_sleep_wakeup_cause_t wakeup_reason;
  wakeup_reason = esp_sleep_get_wakeup_cause();
  switch(wakeup_reason)
  {
    case 1  : Serial.println("Wakeup caused by external signal using RTC_IO"); break;
    case 2  : Serial.println("Wakeup caused by external signal using RTC_CNTL"); break;
    case 3  : Serial.println("Wakeup caused by timer"); break;
    case 4  : Serial.println("Wakeup caused by touchpad"); break;
    case 5  : Serial.println("Wakeup caused by ULP program"); break;
    default : Serial.println("Wakeup was not caused by deep sleep"); break;
  }
}

void print_DHT20_error(int status) {
      switch (status)
    {
      case DHT20_OK:
        Serial.print("OK");
        break;
      case DHT20_ERROR_CHECKSUM:
        Serial.print("Checksum error");
        break;
      case DHT20_ERROR_CONNECT:
        Serial.print("Connect error");
        break;
      case DHT20_MISSING_BYTES:
        Serial.print("Missing bytes");
        break;
      case DHT20_ERROR_BYTES_ALL_ZERO:
        Serial.print("All bytes read zero");
        break;
      case DHT20_ERROR_READ_TIMEOUT:
        Serial.print("Read time out");
        break;
      case DHT20_ERROR_LASTREAD:
        Serial.print("Error read too fast");
        break;
      default:
        Serial.print("Unknown error");
        break;
    }
    Serial.print("\n");
}

bool SW_DHT20_begin()
{
  //  _wire->setWireTimeout(DHT20_WIRE_TIME_OUT, true);
  return SW_DHT20_isConnected();
}


bool SW_DHT20_isConnected()
{
  sw.beginTransmission(DHT20_ADDRESS);
  sw.write(uint8_t(0));
  int rv = sw.endTransmission();
  if (rv) Serial.printf("Not Connected: %d", rv);
  return rv == 0;
}

bool isMeasuring()
{
  return (SW_DHT20_readStatus() & 0x80) == 0x80;
}

int SW_DHT20_read()
{
  //  do not read to fast == more than once per second.
  if (millis() - _lastRead < 1000)
  {
    return DHT20_ERROR_LASTREAD;
  }

  int status = SW_DHT20_requestData();
  if (status < 0) return status;
  //  wait for measurement ready
  uint32_t start = millis();
  while (isMeasuring())
  {
    if (millis() - start >= 1000)
    {
      return DHT20_ERROR_READ_TIMEOUT;
    }
    yield();
  }
  //  read the measurement
  status = SW_DHT20_readData();
  if (status < 0) return status;

  //  convert it to meaningful data
  return SW_DHT20_convert();
}

uint8_t SW_DHT20_readStatus()
{
  sw.requestFrom(DHT20_ADDRESS, (uint8_t)1);
  delay(1);  //  needed to stabilize timing
  return (uint8_t) sw.read();
}

uint8_t SW_DHT20_resetSensor()
{
  uint8_t count = 255;
  if ((SW_DHT20_readStatus() & 0x18) != 0x18)
  {
    count++;
    if (SW_DHT20_resetRegister(0x1B)) count++;
    if (SW_DHT20_resetRegister(0x1C)) count++;
    if (SW_DHT20_resetRegister(0x1E)) count++;
    delay(10);
  }
  return count;
}


int SW_DHT20_requestData()
{
  //  reset sensor if needed.
  SW_DHT20_resetSensor();

  //  GET CONNECTION
  sw.beginTransmission(DHT20_ADDRESS);
  sw.write(0xAC);
  sw.write(0x33);
  sw.write(0x00);
  int rv = sw.endTransmission();

  _lastRequest = millis();
  return rv;
}


int SW_DHT20_readData()
{
  //  GET DATA
  const uint8_t length = 7;
  int bytes = sw.requestFrom(DHT20_ADDRESS, length);

  if (bytes == 0)     return DHT20_ERROR_CONNECT;
  if (bytes < length) return DHT20_MISSING_BYTES;

  bool allZero = true;
  for (int i = 0; i < bytes; i++)
  {
    _bits[i] = sw.read();
    //  if (_bits[i] < 0x10) Serial.print(0);
    //  Serial.print(_bits[i], HEX);
    //  Serial.print(" ");
    allZero = allZero && (_bits[i] == 0);
  }
  //  Serial.println();
  if (allZero) return DHT20_ERROR_BYTES_ALL_ZERO;

  _lastRead = millis();
  return bytes;
}


int SW_DHT20_convert()
{
  //  CONVERT AND STORE
  _status      = _bits[0];
  uint32_t raw = _bits[1];
  raw <<= 8;
  raw += _bits[2];
  raw <<= 4;
  raw += (_bits[3] >> 4);
  _humidity = raw * 9.5367431640625e-5;   // ==> / 1048576.0 * 100%;

  raw = (_bits[3] & 0x0F);
  raw <<= 8;
  raw += _bits[4];
  raw <<= 8;
  raw += _bits[5];
  _temperature = raw * 1.9073486328125e-4 - 50;  //  ==> / 1048576.0 * 200 - 50;

  //  TEST CHECKSUM
  uint8_t _crc = _crc8(_bits, 6);
  //  Serial.print(_crc, HEX);
  //  Serial.print("\t");
  //  Serial.println(_bits[6], HEX);
  if (_crc != _bits[6]) return DHT20_ERROR_CHECKSUM;

  return DHT20_OK;
}

uint8_t _crc8(uint8_t *ptr, uint8_t len)
{
  uint8_t crc = 0xFF;
  while(len--)
  {
    crc ^= *ptr++;
    for (uint8_t i = 0; i < 8; i++)
    {
      if (crc & 0x80)
      {
        crc <<= 1;
        crc ^= 0x31;
      }
      else
      {
        crc <<= 1;
      }
    }
  }
  return crc;
}

bool SW_DHT20_resetRegister(uint8_t reg)
{
  uint8_t value[3];
  sw.beginTransmission(DHT20_ADDRESS);
  sw.write(reg);
  sw.write(0x00);
  sw.write(0x00);
  if (sw.endTransmission() != 0) return false;
  delay(5);

  int bytes = sw.requestFrom(DHT20_ADDRESS, (uint8_t)3);
  for (int i = 0; i < bytes; i++)
  {
    value[i] = sw.read();
    //  Serial.println(value[i], HEX);
  }
  delay(10);

  sw.beginTransmission(DHT20_ADDRESS);
  sw.write(0xB0 | reg);
  sw.write(value[1]);
  sw.write(value[2]);
  if (sw.endTransmission() != 0) return false;
  delay(5);
  return true;
}

//  -- END OF FILE --