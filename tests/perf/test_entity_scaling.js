import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = 'http://localhost:8000/v1/chat';

const ENTITY_COUNT = 100;

function generateEntities(count) {
    let text = "";
    for (let i = 0; i < count; i++) {
        text += `Osoba ${i}: Jan Kowalski PESEL 90010112345 mieszka w Warszawie. `;
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
        max_tokens: 500
    });

    const res = http.post(BASE_URL, payload, {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-key'
        },
    });

    check(res, {
        'status 200': (r) => r.status === 200,
    });
}
