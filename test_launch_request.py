import json
from lambda_function_local import lambda_handler

# Test event for LaunchRequest (opening the skill)
test_event = {
    'version': '1.0',
    'session': {
        'new': True,
        'sessionId': 'amzn1.echo-api.session.test',
        'attributes': {},
        'user': {
            'userId': 'amzn1.ask.account.TESTUSER'
        },
        'application': {
            'applicationId': 'amzn1.ask.skill.test'
        }
    },
    'context': {
        'System': {
            'application': {
                'applicationId': 'amzn1.ask.skill.test'
            },
            'user': {
                'userId': 'amzn1.ask.account.TESTUSER'
            },
            'device': {
                'deviceId': 'amzn1.ask.device.test',
                'supportedInterfaces': {}
            }
        }
    },
    'request': {
        'type': 'LaunchRequest',
        'requestId': 'amzn1.echo-api.request.test',
        'timestamp': '2025-11-01T10:00:00Z',
        'locale': 'pt-BR'
    }
}

# Mock context
class MockContext:
    pass

context = MockContext()

print("=" * 60)
print("Testing Skill Launch (Opening the Skill)")
print("=" * 60)
print("\n📋 Test Event: LaunchRequest")
print("(This is what happens when you say 'Alexa, abrir status da bateria')")

print("\n🚀 Invoking lambda_handler...")
print("-" * 60)

try:
    response = lambda_handler(test_event, context)

    print("\n✅ Response Received:")
    print(json.dumps(response, indent=2))

    # Extract and display the speech text
    speech_text = response.get('response', {}).get('outputSpeech', {}).get('text', '')
    print("\n🎤 Alexa will immediately say:")
    print(f'"{speech_text}"')

    print("\n✨ No more waiting! Battery level shown instantly!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
