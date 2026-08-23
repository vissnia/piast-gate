import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = 'http://localhost:8000/v1/api/chat';

const ENTITY_COUNT = 10;

function generateEntities(count) {
    let text = "";
    for (let i = 0; i < count; i++) {
        text += `Jan Kowalski mieszka w Warszawie przy ul. Kwiatowej. PESEL: 90010112349. Numer telefonu: 123456789. Email: j.kowalski@examp.com. `;
    }
    return text;
}

export const options = {
    vus: 20,
    duration: '30s',
};

export default function () {
    const payload = JSON.stringify({
        model: "mock",
        messages: [
            {
                role: "system",
                content: generateEntities(ENTITY_COUNT),
            }
        ],
        temperature: 0.1,
        max_tokens: 100000
    });

    const res = http.post(BASE_URL, payload, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key'
        },
    });

    check(res, {
        'status 200': (r) => r.status === 200,
    });
}
