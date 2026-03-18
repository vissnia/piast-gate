import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = 'http://localhost:8000/v1/chat';

const MESSAGE_MULTIPLIER = 500;

function generateLongMessage(multiplier) {
    const base = "Jan Kowalski mieszka w Warszawie przy ul. Kwiatowej. PESEL: 90010112345. Numer telefonu: 123456789. Email: j.kowalski@example.com";
    return base.repeat(multiplier);
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
                content: generateLongMessage(MESSAGE_MULTIPLIER),
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