const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();
const PORT = 3000;

app.use(cors()); 
app.use(express.json()); 


const pool = new Pool({
    user: 'myappuser',           
    host: '127.0.0.1',           
    database: 'student_db',
    password: 'password',     
    port: 5432,
});

pool.connect().then(() => {
    console.log('✅ Connected successfully to Data Tier (PostgreSQL) on 5432');
}).catch(err => {
    console.error('❌ DB Connection Error. Check your user/pass and PostgreSQL service:', err.message);
    process.exit(1);
});

app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ success: false, message: 'Username and password are required.' });
    }

    try {
        const result = await pool.query(
            'SELECT password_hash FROM students WHERE username = $1',
            [username]
        );

        if (result.rows.length === 0) {
            return res.status(401).json({ success: false, message: 'Invalid credentials: User not found.' });
        }

        const storedPassword = result.rows[0].password_hash;
        
        if (password === storedPassword) { 
            return res.json({ success: true, message: 'Login successful! Welcome.' });
        } else {
            return res.status(401).json({ success: false, message: 'Invalid credentials: Password mismatch.' });
        }

    } catch (error) {
        console.error('Internal Server Error:', error.message);
        return res.status(500).json({ success: false, message: 'Internal server error.' });
    }
});


app.listen(PORT, '127.0.0.1', () => { 
    console.log(`🚀 Application Tier (Backend) running on http://127.0.0.1:${PORT}`);
    console.log(`Presentation Tier will talk to this address.`);
});
