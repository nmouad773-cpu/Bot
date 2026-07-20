const axios = require("axios");
const { spawn } = require("child_process");

const GRAPH_VERSION = "v19.0";

// --- بيانات الوصول للبث المباشر ---
const LIVE_ACCESS_TOKEN = "EAAcF6ZCku30kBSBa0nfvU8t2WEgWhA8wqC2scnRP6IIFbSsnrbmE0QvAHTj8or5blfnifnK26eicPGFVksHat0INGZBoRfkX8PkZB9ZB4MaDLlH08HGZC85YZCZCBcDCWsrNCNiwobWjZAyOTwEg293ZBXta8WsgEIZAaZBX89OI1l7ZAmD1h15u0xIF0Rj9a0cPpV3MI4lZC";
const LIVE_PAGE_ID      = "466039649924341"; 

// --- بيانات الوصول لتعديل المنشور ---
const POST_ACCESS_TOKEN = "EAAcF6ZCku30kBSHnHqOq0afqZAPq5PFWTLPlXg35ZAz7ygcRTfAwjXkNUqTeZCTcSbrdxpZCtZCOG8kNnW87JZBakvHqXapw0Uiy2aRvBSu6VZBPqHAaBjZBUebDVdjSI4znZCve5ZBHfoJZBPWTkY8bVLNfDjEbTzNLonYCpUOfPD4vazwZBdBjIs7F0ZBlQnm5avqDkxGlblf50d";
const POST_PAGE_ID      = "1288067541053277";
const POST_ID           = "122100265965401514";

// --- قائمة القنوات الشاملة ---
const CHANNELS = [
    { 
        name: "beIN 1",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40215.ts",  
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/751563664_122100376317401514_7110231260316540204_n.jpg?stp=dst-jpg_tt6&cstp=mx447x447&ctp=s447x447&_nc_cat=102&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=TLpTgiehBq8Q7kNvwG7e6fr&_nc_oc=Adphwie250_LoPza4kadv_EOltqLTSHDBw0vTUdHWHFNAOZr7ZbvkYmYNJxlPtX1Nsg&_nc_zt=23&_nc_ht=scontent.fcmn7-1.fna&_nc_gid=yEEgc5683cYLvXmaIGKcfQ&_nc_ss=7b289&oh=00_AQAhfQL5H2WsQlyG_D71zMMeKFFA9RnABtcAqsxKzh-thg&oe=6A644D8D" 
    },
    { 
        name: "beIN 2",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40216.ts",  
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/752551212_122100376689401514_5886627502394995910_n.jpg?stp=dst-jpg_tt6&cstp=mx200x200&ctp=s200x200&_nc_cat=110&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=z4nwcj0ViHAQ7kNvwGOSJZT&_nc_oc=Adq586Y8gkrlvsyde8q1ofxnj-vZTFewhbFYd-C33-ZcX_0zMI7eYSx-zvsV_WTlU7o&_nc_zt=23&_nc_ht=scontent.fcmn5-1.fna&_nc_gid=t6wQiIQ6Lgb5HIe5s_vUjQ&_nc_ss=7b289&oh=00_AQA7J-qLVQlAdHngD7FdSaHsGqqaOMlPTFsZpJFftj1oPw&oe=6A64566A" 
    },
    { 
        name: "beIN 3",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40218.ts",  
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/752484584_122100376671401514_6217817104784997284_n.jpg?stp=dst-jpg_tt6&cstp=mx447x447&ctp=s447x447&_nc_cat=102&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=fOqozvThvhAQ7kNvwEb1Np0&_nc_oc=AdosbWce7blAiqo3Mm1AzHCQDO2iRGB2k5F0fFJUFnsvmR1wGXL-7xF2TwsHzeHU3kE&_nc_zt=23&_nc_ht=scontent.fcmn7-1.fna&_nc_gid=m1_yQa9AEA1qypn-tsV1sg&_nc_ss=7b289&oh=00_AQCm4-EHHUYAybxgWRiI1m19uBwrgqUEEFoA_LBnUbbR5Q&oe=6A645D42" 
    },
    { 
        name: "beIN 4",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40219.ts",  
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/751578454_122100376809401514_6895915391964971655_n.jpg?stp=dst-jpg_tt6&cstp=mx200x200&ctp=s200x200&_nc_cat=107&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=N2_PjpxatqoQ7kNvwEGl66q&_nc_oc=AdqWD1jd9bNexUcSdXFXeUxcrctpwOXg3128503HXgA33sV4EXcyezbqV4Np-zbAPvo&_nc_zt=23&_nc_ht=scontent.fcmn7-1.fna&_nc_gid=l6UqIvNuGWGlm7ahim2MZw&_nc_ss=7b289&oh=00_AQAdgJXZn7fb-ItD4VaIqhv3cYhw-NyHL5jxnW1l9ay_yQ&oe=6A64580A" 
    },
    { 
        name: "beIN 5",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40220.ts",  
        img: "https://scontent.fcmn7-1.fna.fbcdn.net/v/t39.30808-6/751437753_122100376821401514_6360876051451700135_n.jpg?stp=dst-jpg_tt6&cstp=mx200x200&ctp=s200x200&_nc_cat=109&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=ySobcf3DHjkQ7kNvwGm3gSt&_nc_oc=Ado8vcCfuFeOm6-dxHj3wsm1gf1IY5908s2xroXCh910--xCnep4DEti4ZuzxISFN40&_nc_zt=23&_nc_ht=scontent.fcmn7-1.fna&_nc_gid=oFMQ7vCvjHGEMBFv19j2Gw&_nc_ss=7b289&oh=00_AQD5-Kj5qOCMqKBJtM5xumrJNcSHsp9IMFZqhhZrevqjbA&oe=6A647F38" 
    },
    { 
        name: "beIN 6",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40221.ts",  
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/753647362_122100376815401514_2257212559810435923_n.jpg?stp=dst-jpg_tt6&cstp=mx200x200&ctp=s200x200&_nc_cat=103&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=pwxaqOFDXHUQ7kNvwGlavHZ&_nc_oc=Ado93-Ao-Uafm_24GAs4QEQmtqyDR4XfEStTwKNX8pyRJlRDBp9TEfeldrnXF7bqKw8&_nc_zt=23&_nc_ht=scontent.fcmn7-1.fna&_nc_gid=qIBJdlGIwLWJdiDSPlyu3g&_nc_ss=7b289&oh=00_AQBl7HqKUgm-hnksxvW0JrNEKRpEEDLe435LHTZ5sZvP0g&oe=6A647B84" 
    },
    { 
        name: "beIN 7",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40222.ts",  
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/753320194_122100376683401514_6123074156123600585_n.jpg?stp=dst-jpg_tt6&cstp=mx200x200&ctp=s200x200&_nc_cat=111&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=OzhXdnr9YFQQ7kNvwHCQok4&_nc_oc=AdpT4gQOHsVhF9Jsw1IlRYGK870LCY65rY88epGZ1PyBTg_X9gbUqQYn-taGp00xSFU&_nc_zt=23&_nc_ht=scontent.fcmn5-2.fna&_nc_gid=F4Mg_1myT-o5kIICu54igw&_nc_ss=7b289&oh=00_AQC6H5KnvrMNh1LnVcj6qi-TKTNFNO_bFUg1LCnp78KCeg&oe=6A646CA6" 
    },
    { 
        name: "beIN 8",    
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/40223.ts",  
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/751915199_122100376731401514_3271433633498970370_n.jpg?stp=dst-jpg_tt6&cstp=mx200x200&ctp=s200x200&_nc_cat=104&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=SCHI_I1ewfcQ7kNvwEhQdSZ&_nc_oc=AdoIIL7hD1GJXzP187-mP1lbKbJ-bFOKapcCqF2Iw7DcQPwqnRIzdaV51VCEXScSz8w&_nc_zt=23&_nc_ht=scontent.fcmn5-2.fna&_nc_gid=2s0C_xunuHkudQhNlPTuDA&_nc_ss=7b289&oh=00_AQCq_eQehzRfTiLB6GDirN9AjDjx8nb10SsclXjKhRLMEA&oe=6A647DF6" 
    },
    { 
        name: "beIN News", 
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/256952.ts", 
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/753320194_122100376827401514_8275779885008593037_n.jpg?stp=dst-jpg_tt6&cstp=mx200x200&ctp=s200x200&_nc_cat=104&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=Z1L3joJIsbAQ7kNvwE-yaFq&_nc_oc=Adp37Drggm4JsIEa_bDP3atBnWXnz9dB58hBEpxXEh5u3hayJ1uiUkOGUnCqQJ-DaUw&_nc_zt=23&_nc_ht=scontent.fcmn5-1.fna&_nc_gid=HTDMSiG_KoRIadFytuAx-Q&_nc_ss=7b289&oh=00_AQBepozuMy5zvH_u-B_hQK19qg3OZrdaF-uGU9YxubJT7w&oe=6A6476B7" 
    },
    { 
        name: "الثمانية 1", 
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/283461.ts", 
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/752648857_122100395247401514_7968696883797853697_n.jpg?stp=dst-jpg_tt6&cstp=mx240x240&ctp=s240x240&_nc_cat=109&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=2FRLcPqDq_cQ7kNvwEXeapC&_nc_oc=AdpXohEoQ7ZJmb3FvdIif-lHhpFlq8DqVZpSfLUom1XR48oQuFzdVebk1QiK1HZEAzU&_nc_zt=23&_nc_ht=scontent.fcmn5-1.fna&_nc_gid=-kptSb0bXqpmqziwEiUyqg&_nc_ss=7b289&oh=00_AQBQFybFXkZv6AM5d3oYYfbgH_4dQ7pbGTALBAzsfbDsTQ&oe=6A645902" 
    },
    { 
        name: "الثمانية 2", 
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/283464.ts", 
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/752648857_122100395247401514_7968696883797853697_n.jpg?stp=dst-jpg_tt6&cstp=mx240x240&ctp=s240x240&_nc_cat=109&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=2FRLcPqDq_cQ7kNvwEXeapC&_nc_oc=AdpXohEoQ7ZJmb3FvdIif-lHhpFlq8DqVZpSfLUom1XR48oQuFzdVebk1QiK1HZEAzU&_nc_zt=23&_nc_ht=scontent.fcmn5-1.fna&_nc_gid=-kptSb0bXqpmqziwEiUyqg&_nc_ss=7b289&oh=00_AQBQFybFXkZv6AM5d3oYYfbgH_4dQ7pbGTALBAzsfbDsTQ&oe=6A645902" 
    },
    { 
        name: "الثمانية 3", 
        url: "http://mavpro.xyz:8080/live/8454745cdsdw/8455144xsfdd/283467.ts", 
        img: "https://scontent.xx.fbcdn.net/v/t39.30808-6/752648857_122100395247401514_7968696883797853697_n.jpg?stp=dst-jpg_tt6&cstp=mx240x240&ctp=s240x240&_nc_cat=109&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=833d8c&_nc_ohc=2FRLcPqDq_cQ7kNvwEXeapC&_nc_oc=AdpXohEoQ7ZJmb3FvdIif-lHhpFlq8DqVZpSfLUom1XR48oQuFzdVebk1QiK1HZEAzU&_nc_zt=23&_nc_ht=scontent.fcmn5-1.fna&_nc_gid=-kptSb0bXqpmqziwEiUyqg&_nc_ss=7b289&oh=00_AQBQFybFXkZv6AM5d3oYYfbgH_4dQ7pbGTALBAzsfbDsTQ&oe=6A645902" 
    }
];

// --- الإعدادات الزمنية (3 ساعات و 5 دقائق لكل دورة) ---
const SESSION_MS  = (3 * 60 + 5) * 60 * 1000; 
const MPD_WAIT_MS = 2 * 60 * 1000;            
const COOLDOWN_MS = 1 * 60 * 1000;            

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function formatDuration(ms) {
    const s = Math.floor(ms / 1000);
    return `${Math.floor(s/3600)}h ${Math.floor((s%3600)/60)}m ${s%60}s`;
}

function nowStr() {
    return new Date().toISOString().replace("T", " ").slice(0, 19);
}

async function countdown(ms, label) {
    let rem = ms;
    while (rem > 0) {
        process.stdout.write(`\r    ${label}: ${formatDuration(rem)}   `);
        const step = Math.min(1000, rem);
        await sleep(step);
        rem -= step;
    }
    console.log("");
}

// --- دالة تشغيل FFmpeg مع توجيه مباشر بدون User-Agent وبدون إعادة ترميز ---
function startFFmpeg(channel, rtmp) {
    const args = [
        "-re",
        "-i", channel.url,
        "-c", "copy", 
        "-f", "flv",
        rtmp
    ];

    const proc = spawn("ffmpeg", args, { stdio: "ignore" });
    
    proc.on("exit", (code) => {
        if (code !== 0 && code !== null) {
            console.log(`  ⚠️ [${channel.name}] توقف كود الخروج: ${code}`);
        }
    });

    return proc;
}

async function createPreview(channel) {
    try {
        const res = await axios.post(
            `https://graph.facebook.com/${GRAPH_VERSION}/${LIVE_PAGE_ID}/live_videos`,
            null,
            {
                timeout: 15000,
                params: { access_token: LIVE_ACCESS_TOKEN, status: "UNPUBLISHED", title: channel.name }
            }
        );
        console.log(`  ✅ [${channel.name}] جاهز (ID: ${res.data.id})`);
        return { ...channel, ...res.data };
    } catch (e) {
        console.error(`  ❌ [${channel.name}] فشل الإنشاء: ${e.response?.data?.error?.message || e.message}`);
        return null;
    }
}

async function deleteLiveVideo(videoId) {
    try {
        await axios.delete(`https://graph.facebook.com/${GRAPH_VERSION}/${videoId}`, {
            params: { access_token: LIVE_ACCESS_TOKEN },
            timeout: 10000
        });
        console.log(`  🗑️ تم حذف البث المباشر القديم (ID: ${videoId})`);
    } catch (e) {
        console.error(`  ⚠️ فشل حذف البث ${videoId}: ${e.response?.data?.error?.message || e.message}`);
    }
}

async function updatePost(streamKeys) {
    const updatedData = streamKeys.map(s => ({
        img:  s.img,
        name: s.name,
        url:  s.dash || "Offline", 
    }));

    const message = JSON.stringify(updatedData);

    try {  
        await axios.post(  
            `https://graph.facebook.com/${GRAPH_VERSION}/${POST_PAGE_ID}_${POST_ID}`,  
            null,  
            { params: { access_token: POST_ACCESS_TOKEN, message: message } }  
        );  
        console.log(`  📝 تم تحديث روابط القنوات والصور في المنشور بنجاح`);  
    } catch (e) {  
        console.error(`  ⚠️ [POST] خطأ أثناء تحديث المنشور: ${e.response?.data?.error?.message || e.message}`);  
    }
}

async function runSession(cycleNum) {
    const sessionStart = Date.now();
    console.log(`\n${"=".repeat(40)}`);
    console.log(`🔄 الدورة #${cycleNum} | بدأت في: ${nowStr()}`);
    console.log(`${"=".repeat(40)}`);

    console.log(`\n1️⃣ إنشاء بثوث Facebook بالتوازي...`);  
    const sessions = (await Promise.all(CHANNELS.map(createPreview))).filter(Boolean);  

    console.log(`\n2️⃣ تشغيل محركات البث (FFmpeg) لجميع القنوات معاً...`);  
    const streamKeys = [];  
    const procs = [];  

    sessions.forEach(res => {  
        if (res?.stream_url) {  
            const info = { name: res.name, url: res.url, img: res.img, rtmp: res.stream_url, id: res.id };  
            streamKeys.push(info);  
            procs.push(startFFmpeg(info, info.rtmp));  
        }  
    });  

    if (procs.length === 0) {
        console.log("  ⚠️ لم يتم إنشاء أي جلسات بث، تخطي الدورة...");
        return;
    }

    console.log(`\n3️⃣ انتظار استقرار البث لتوليد روابط DASH...`);  
    await countdown(MPD_WAIT_MS, "⏰ المتبقي");  

    console.log(`\n4️⃣ جلب روابط DASH (MPD) لكل القنوات بالتوازي وتحديث المنشور...`);  
    await Promise.all(streamKeys.map(async (s) => {
        try {  
            const r = await axios.get(  
                `https://graph.facebook.com/${GRAPH_VERSION}/${s.id}`,  
                { 
                    params: { fields: "dash_preview_url", access_token: LIVE_ACCESS_TOKEN },
                    timeout: 10000
                }  
            );  
            s.dash = r.data.dash_preview_url || null;  
        } catch { 
            s.dash = null; 
        }  
    }));

    await updatePost(streamKeys);  

    const remaining = SESSION_MS - (Date.now() - sessionStart);  
    if (remaining > 0) {  
        console.log(`\n🚀 جميع البثوث تعمل والمنشور محدث! وقت البث الحالي (3 ساعات و 5 دقائق)...`);  
        await countdown(remaining, "⏰ وقت انتهاء البث القادم");  
    }  

    console.log(`\n5️⃣ إيقاف الجلسة، حذف البثوث القديمة وتنظيف العمليات...`);  
    procs.forEach(p => { try { p.kill("SIGKILL"); } catch {} });  
    try { require("child_process").execSync("pkill -9 ffmpeg 2>/dev/null || true"); } catch {}

    await Promise.all(streamKeys.map(s => deleteLiveVideo(s.id)));
}

async function main() {
    console.clear();
    console.log("==========================================");
    console.log("   Facebook Live Multi-Streamer 24/7      ");
    console.log("==========================================\n");

    let cycle = 1;  
    while (true) {  
        try {  
            await runSession(cycle);  
        } catch (err) {  
            console.error(`❌ خطأ غير متوقع: ${err.message}`);  
            try { require("child_process").execSync("pkill -9 ffmpeg 2>/dev/null || true"); } catch {}  
        }  

        console.log(`\n💤 فترة راحة سريعة (دقيقة واحدة) قبل البدء في الدورة التالية...`);  
        await countdown(COOLDOWN_MS, "⏰ العودة بعد");  
        cycle++;  
    }
}

main();
