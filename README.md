# Ask Battery - Alexa Skill

An Alexa Skill that allows users to check the battery level of their Deye inverter by simply asking. The skill connects to the Deye inverter API and provides real-time battery information.

## Features

- **Voice Control**: Ask Alexa for your battery level using natural language
- **Real-time Data**: Connects directly to the Deye inverter to fetch current battery status
- **Simple Integration**: Easy setup with Alexa-enabled devices

## How It Works

1. User asks Alexa for the battery level
2. The skill authenticates with the Deye inverter
3. Fetches the current battery level from the inverter
4. Alexa responds with the battery status

## Requirements

- Alexa-enabled device
- Deye inverter with API access
- Deye inverter credentials (IP address, username, password)

## Setup

1. Clone this repository
2. Configure your Deye inverter credentials
3. Deploy the skill to AWS Lambda
4. Configure the Alexa skill in the Alexa Developer Console
5. Link your inverter in the skill settings

## Usage

Simply say to your Alexa device:

- "Alexa, ask Battery what's the battery level"
- "Alexa, ask Battery for battery status"
- "Alexa, what's my battery level"

## Project Structure

```
ask-battery/
├── README.md
├── lambda_function.py
└── requirements.txt
```

## Technologies

- **Alexa Skills Kit (ASK)**: For Alexa skill development
- **AWS Lambda**: For hosting the skill backend
- **Deye Inverter API**: For battery level data

## License

MIT
