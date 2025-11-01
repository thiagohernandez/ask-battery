import json
import requests
import os
import hashlib
import time

# Cache for access token (reused across Lambda invocations)
token_cache = {
    'access_token': None,
    'expires_at': 0
}

def lambda_handler(event, context):
    """
    Main Lambda handler for Alexa Skill with Deye Cloud API
    """
    request_type = event['request']['type']
    
    # Check if device supports APL (for visual display)
    has_display = 'Alexa.Presentation.APL' in event['context']['System']['device']['supportedInterfaces']
    
    if request_type == "LaunchRequest":
        return build_response(
            "Bem-vindo ao Monitor de Bateria. Pergunte-me sobre o nível da sua bateria.",
            has_display=has_display
        )
    
    elif request_type == "IntentRequest":
        intent_name = event['request']['intent']['name']
        
        if intent_name == "GetBatteryStatus":
            return get_battery_status(has_display)
        
        elif intent_name == "AMAZON.HelpIntent":
            return build_response("Você pode me perguntar: qual é o percentual da minha bateria?", has_display=has_display)
        
        elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
            return build_response("Adeus!", should_end=True, has_display=has_display)

    return build_response("Não entendi isso. Por favor, tente novamente.", has_display=has_display)


def get_access_token():
    """
    Get or refresh Deye Cloud access token
    """
    # Check if cached token is still valid
    current_time = int(time.time())
    if token_cache['access_token'] and token_cache['expires_at'] > current_time:
        return token_cache['access_token']

    # Request new token
    api_url = os.environ.get('DEYE_API_URL', 'https://eu1-developer.deyecloud.com/')
    api_url = api_url.rstrip('/')  # Remove trailing slash for proper concatenation
    app_id = os.environ.get('DEYE_APP_ID')
    token_url = f"{api_url}/v1.0/account/token?appId={app_id}"

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        "appSecret": os.environ.get('DEYE_APP_SECRET'),
        "email": os.environ.get('DEYE_EMAIL'),
        "password": os.environ.get('DEYE_PASSWORD_HASH')  # Must be SHA256 hash (lowercase)
    }

    try:
        response = requests.post(token_url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if result.get('code') == '0' or result.get('success'):
            access_token = result['data']['access_token']
            expires_in = result['data'].get('expires_in', 7200)  # Default 2 hours
            
            # Cache the token
            token_cache['access_token'] = access_token
            token_cache['expires_at'] = current_time + expires_in - 300  # Refresh 5 min early
            
            return access_token
        else:
            print(f"Token error: {result}")
            return None
            
    except Exception as e:
        print(f"Token request error: {str(e)}")
        return None


def get_battery_status(has_display=False):
    """
    Fetch battery status from Deye inverter
    """
    try:
        # Get access token
        access_token = get_access_token()

        if not access_token:
            return build_response(
                "Desculpe, não consegui conectar ao seu inversor. Por favor, verifique suas credenciais.",
                has_display=has_display
            )

        # Get station data using the correct endpoint
        api_url = os.environ.get('DEYE_API_URL', 'https://eu1-developer.deyecloud.com/')
        api_url = api_url.rstrip('/')
        station_url = f"{api_url}/v1.0/station/latest"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        station_payload = {
            "stationId": int(os.environ.get('DEYE_STATION_ID'))
        }

        response = requests.post(station_url, json=station_payload, headers=headers, timeout=10)
        result = response.json()

        print(f"API Response: {result}")  # For debugging

        if result.get('code') != '1000000' and not result.get('success'):
            return build_response(
                "Desculpe, não consegui recuperar os dados da sua bateria.",
                has_display=has_display
            )

        # Extract battery data from response (data is at top level, not nested)
        # Common field names in Deye API:
        battery_percent = (
            result.get('batterySoc') or
            result.get('battery_soc') or
            result.get('batterySOC') or
            0
        )

        battery_power = (
            result.get('batteryPower') or
            result.get('battery_power') or
            0
        )

        solar_power = (
            result.get('generationPower') or
            result.get('generation_power') or
            result.get('pvPower') or
            0
        )

        grid_power = (
            result.get('gridPower') or
            result.get('grid_power') or
            0
        )

        consumption_power = (
            result.get('consumptionPower') or
            result.get('consumption_power') or
            0
        )

        battery_percent = int(battery_percent)
        battery_power = int(battery_power)
        solar_power = int(solar_power)
        grid_power = int(grid_power) if grid_power else 0
        consumption_power = int(consumption_power)

        speech_text = f"A bateria da sua casa está em {battery_percent} por cento."

        if battery_power > 50:
            speech_text += f" Está carregando em {battery_power} watts."
        elif battery_power < -50:
            speech_text += f" Está descarregando em {abs(battery_power)} watts."

        return build_battery_response(
            speech_text=speech_text,
            battery_percent=battery_percent,
            battery_power=battery_power,
            solar_power=solar_power,
            grid_power=grid_power,
            consumption_power=consumption_power,
            has_display=has_display
        )
        
    except requests.exceptions.Timeout:
        return build_response(
            "Desculpe, a requisição expirou. Por favor, tente novamente.",
            has_display=has_display
        )

    except Exception as e:
        print(f"Erro: {str(e)}")
        return build_response(
            "Desculpe, encontrei um erro ao recuperar o status da sua bateria.",
            has_display=has_display
        )


def build_battery_response(speech_text, battery_percent, battery_power, solar_power, 
                          grid_power, consumption_power, has_display):
    """
    Build response with APL display for Echo Show
    """
    response = {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech_text
            },
            'shouldEndSession': True
        }
    }
    
    # Add visual display for devices with screens
    if has_display:
        response['response']['directives'] = [
            {
                'type': 'Alexa.Presentation.APL.RenderDocument',
                'version': '1.8',
                'document': get_apl_document(),
                'datasources': {
                    'batteryData': {
                        'batteryPercent': int(battery_percent),
                        'batteryPower': int(battery_power),
                        'solarPower': int(solar_power),
                        'gridPower': int(grid_power),
                        'consumptionPower': int(consumption_power),
                        'status': get_battery_status_text(battery_percent),
                        'color': get_battery_color(battery_percent),
                        'batteryState': get_battery_state(battery_power)
                    }
                }
            }
        ]
    
    return response


def get_battery_color(percent):
    """Return color based on battery level"""
    if percent >= 80:
        return '#00FF00'  # Green
    elif percent >= 50:
        return '#FFA500'  # Orange
    elif percent >= 20:
        return '#FF6B00'  # Dark Orange
    else:
        return '#FF0000'  # Red


def get_battery_status_text(percent):
    """Return status text based on battery level"""
    if percent >= 80:
        return 'Totalmente Carregado'
    elif percent >= 50:
        return 'Bom'
    elif percent >= 20:
        return 'Médio'
    else:
        return 'Baixo - Considere Carregar'


def get_battery_state(power):
    """Return battery state based on power flow"""
    if power > 50:
        return '⚡ Carregando'
    elif power < -50:
        return '🔋 Descarregando'
    else:
        return '⏸️ Inativo'


def get_apl_document():
    """
    APL Document for Echo Show visual display
    """
    return {
        'type': 'APL',
        'version': '1.8',
        'theme': 'dark',
        'mainTemplate': {
            'parameters': ['batteryData'],
            'items': [
                {
                    'type': 'Container',
                    'width': '100vw',
                    'height': '100vh',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'items': [
                        {
                            'type': 'Container',
                            'width': '90vw',
                            'height': '85vh',
                            'direction': 'column',
                            'alignItems': 'center',
                            'justifyContent': 'spaceAround',
                            'items': [
                                # Title
                                {
                                    'type': 'Text',
                                    'text': 'Status da Bateria',
                                    'fontSize': '50dp',
                                    'fontWeight': 'bold',
                                    'color': '#FFFFFF'
                                },
                                # Battery visualization
                                {
                                    'type': 'Container',
                                    'direction': 'column',
                                    'alignItems': 'center',
                                    'items': [
                                        # Battery icon frame
                                        {
                                            'type': 'Frame',
                                            'width': '280dp',
                                            'height': '140dp',
                                            'borderWidth': '6dp',
                                            'borderColor': '${batteryData.color}',
                                            'borderRadius': '15dp',
                                            'items': [
                                                # Fill level
                                                {
                                                    'type': 'Frame',
                                                    'width': '${(batteryData.batteryPercent * 2.68)}dp',
                                                    'height': '100%',
                                                    'backgroundColor': '${batteryData.color}',
                                                    'borderRadius': '10dp'
                                                }
                                            ]
                                        },
                                        # Battery terminal
                                        {
                                            'type': 'Frame',
                                            'width': '35dp',
                                            'height': '18dp',
                                            'backgroundColor': '${batteryData.color}',
                                            'position': 'absolute',
                                            'left': '305dp',
                                            'top': '61dp'
                                        },
                                        # Percentage
                                        {
                                            'type': 'Text',
                                            'text': '${batteryData.batteryPercent}%',
                                            'fontSize': '100dp',
                                            'fontWeight': 'bold',
                                            'color': '${batteryData.color}',
                                            'paddingTop': '30dp'
                                        },
                                        # Status
                                        {
                                            'type': 'Text',
                                            'text': '${batteryData.status}',
                                            'fontSize': '35dp',
                                            'color': '#CCCCCC'
                                        },
                                        # Battery state
                                        {
                                            'type': 'Text',
                                            'text': '${batteryData.batteryState}',
                                            'fontSize': '30dp',
                                            'color': '#AAAAAA',
                                            'paddingTop': '10dp'
                                        }
                                    ]
                                },
                                # Stats grid
                                {
                                    'type': 'Container',
                                    'direction': 'row',
                                    'width': '85vw',
                                    'justifyContent': 'spaceAround',
                                    'items': [
                                        # Solar Power
                                        {
                                            'type': 'Container',
                                            'direction': 'column',
                                            'alignItems': 'center',
                                            'items': [
                                                {
                                                    'type': 'Text',
                                                    'text': '☀️ Solar',
                                                    'fontSize': '25dp',
                                                    'color': '#AAAAAA'
                                                },
                                                {
                                                    'type': 'Text',
                                                    'text': '${batteryData.solarPower} W',
                                                    'fontSize': '32dp',
                                                    'fontWeight': 'bold',
                                                    'color': '#FFD700'
                                                }
                                            ]
                                        },
                                        # Grid Power
                                        {
                                            'type': 'Container',
                                            'direction': 'column',
                                            'alignItems': 'center',
                                            'items': [
                                                {
                                                    'type': 'Text',
                                                    'text': '🔌 Rede',
                                                    'fontSize': '25dp',
                                                    'color': '#AAAAAA'
                                                },
                                                {
                                                    'type': 'Text',
                                                    'text': '${batteryData.gridPower} W',
                                                    'fontSize': '32dp',
                                                    'fontWeight': 'bold',
                                                    'color': '#00BFFF'
                                                }
                                            ]
                                        },
                                        # Consumption
                                        {
                                            'type': 'Container',
                                            'direction': 'column',
                                            'alignItems': 'center',
                                            'items': [
                                                {
                                                    'type': 'Text',
                                                    'text': '🏠 Consumo',
                                                    'fontSize': '25dp',
                                                    'color': '#AAAAAA'
                                                },
                                                {
                                                    'type': 'Text',
                                                    'text': '${batteryData.consumptionPower} W',
                                                    'fontSize': '32dp',
                                                    'fontWeight': 'bold',
                                                    'color': '#FF6B6B'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }


def build_response(speech_text, should_end=True, has_display=False):
    """Build simple Alexa response"""
    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech_text
            },
            'shouldEndSession': should_end
        }
    }