import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = 'http://localhost:8000/chat';

export const options = {
    stages: [
        { duration: '10s', target: 10 },
        { duration: '20s', target: 50 },
        { duration: '20s', target: 100 },
        { duration: '10s', target: 0 },
    ],
};

const payload = JSON.stringify({
    model: "mock",
    messages: [
        {
            role: "system",
            content: "Jan Kowalski mieszka w Warszawie przy ul. Kwiatowej. PESEL: 90010112345. Numer telefonu: 123456789. Email: j.kowalski@example.com",
        }
    ],
    temperature: 0.1,
    max_tokens: 500
});

export default function () {
    const res = http.post(BASE_URL, payload, {
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test-key' },
    });

    check(res, {
        'status 200': (r) => r.status === 200,
    });
}
