class Game {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width;
        this.height = this.canvas.height;

        this.gameState = 'start'; // start, playing, finished
        this.keys = {};
        this.player = null;
        this.opponents = [];
        this.items = [];
        this.roadSegments = [];
        this.lap = 1;
        this.maxLaps = 3;
        this.startTime = 0;
        this.elapsedTime = 0;
        this.playerItem = null;

        this.setupInputHandlers();
        this.initRoad();
        this.draw();
    }

    setupInputHandlers() {
        document.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;
            if (e.key === ' ') {
                e.preventDefault();
                this.useItem();
            }
            if (e.key === 'r' || e.key === 'R') {
                this.restart();
            }
        });

        document.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });
    }

    initRoad() {
        // 道路セグメントを初期化（3D風の効果のため）
        const segmentHeight = 10;
        const totalSegments = 150;

        for (let i = 0; i < totalSegments; i++) {
            // カーブを追加
            const curve = Math.sin(i / 20) * 0.5;
            this.roadSegments.push({
                index: i,
                curve: curve,
                y: i * segmentHeight,
                color: i % 2 === 0 ? '#404040' : '#505050'
            });
        }
    }

    start() {
        document.getElementById('startScreen').classList.add('hidden');
        this.gameState = 'playing';
        this.startTime = Date.now();

        // プレイヤーのカートを初期化
        this.player = new Kart(this.width / 2, this.height - 150, '#ff0000', true);

        // 対戦相手を初期化
        this.opponents = [];
        const colors = ['#0000ff', '#00ff00', '#ffff00', '#ff00ff', '#00ffff'];
        for (let i = 0; i < 5; i++) {
            const x = this.width / 2 + (i - 2) * 80;
            const y = this.height - 200 - (i + 1) * 50;
            this.opponents.push(new Kart(x, y, colors[i], false));
        }

        // アイテムをランダムに配置
        this.spawnItems();

        this.gameLoop();
    }

    spawnItems() {
        this.items = [];
        for (let i = 0; i < 10; i++) {
            const x = Math.random() * (this.width - 100) + 50;
            const y = Math.random() * 1000 + 100;
            const types = ['speed', 'missile', 'shield'];
            const type = types[Math.floor(Math.random() * types.length)];
            this.items.push(new Item(x, y, type));
        }
    }

    useItem() {
        if (!this.playerItem || this.gameState !== 'playing') return;

        switch (this.playerItem.type) {
            case 'speed':
                this.player.boost();
                break;
            case 'missile':
                this.fireMissile();
                break;
            case 'shield':
                this.player.shield = true;
                setTimeout(() => this.player.shield = false, 5000);
                break;
        }

        this.playerItem = null;
        this.updateUI();
    }

    fireMissile() {
        // 最も近い前方の敵を攻撃
        let target = null;
        let minDistance = Infinity;

        for (const opponent of this.opponents) {
            if (opponent.y < this.player.y) {
                const distance = this.player.y - opponent.y;
                if (distance < minDistance) {
                    minDistance = distance;
                    target = opponent;
                }
            }
        }

        if (target) {
            target.hit();
        }
    }

    gameLoop() {
        if (this.gameState !== 'playing') return;

        this.update();
        this.draw();
        this.updateUI();

        requestAnimationFrame(() => this.gameLoop());
    }

    update() {
        // プレイヤーの更新
        if (this.keys['ArrowUp']) {
            this.player.accelerate();
        } else if (this.keys['ArrowDown']) {
            this.player.brake();
        } else {
            this.player.decelerate();
        }

        if (this.keys['ArrowLeft']) {
            this.player.moveLeft();
        }
        if (this.keys['ArrowRight']) {
            this.player.moveRight();
        }

        this.player.update(this.width);

        // 対戦相手の更新（AI）
        for (const opponent of this.opponents) {
            opponent.updateAI(this.width);
        }

        // アイテムとの衝突判定
        for (let i = this.items.length - 1; i >= 0; i--) {
            const item = this.items[i];
            if (this.checkCollision(this.player, item)) {
                if (!this.playerItem) {
                    this.playerItem = item;
                    this.items.splice(i, 1);
                }
            }
        }

        // ラップカウント
        if (this.player.distance > 1500) {
            this.player.distance = 0;
            this.lap++;

            if (this.lap > this.maxLaps) {
                this.finish();
            }
        }

        // 時間の更新
        this.elapsedTime = Date.now() - this.startTime;
    }

    checkCollision(obj1, obj2) {
        const dx = obj1.x - obj2.x;
        const dy = obj1.y - obj2.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        return distance < 30;
    }

    draw() {
        // 背景（空）
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.height);
        gradient.addColorStop(0, '#87ceeb');
        gradient.addColorStop(1, '#ffffff');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.width, this.height);

        // 道路を描画
        this.drawRoad();

        // アイテムを描画
        for (const item of this.items) {
            item.draw(this.ctx);
        }

        // 対戦相手を描画（距離順）
        const allKarts = [...this.opponents, this.player].sort((a, b) => a.y - b.y);
        for (const kart of allKarts) {
            kart.draw(this.ctx);
        }
    }

    drawRoad() {
        const roadWidth = 400;
        const centerX = this.width / 2;

        // 道路の遠近法効果
        for (let i = 0; i < 30; i++) {
            const perspective = i / 30;
            const y = this.height * 0.3 + perspective * this.height * 0.7;
            const width = roadWidth * (0.3 + perspective * 0.7);
            const segmentIndex = Math.floor(this.player.distance / 50 + i);
            const segment = this.roadSegments[segmentIndex % this.roadSegments.length];

            // 道路
            this.ctx.fillStyle = segment.color;
            this.ctx.fillRect(
                centerX - width / 2 + segment.curve * 50 * perspective,
                y,
                width,
                20
            );

            // 白線
            if (segmentIndex % 5 === 0) {
                this.ctx.fillStyle = '#ffffff';
                this.ctx.fillRect(
                    centerX - 5 + segment.curve * 50 * perspective,
                    y + 5,
                    10,
                    10
                );
            }

            // 道路の端
            this.ctx.fillStyle = '#ff0000';
            const edgeWidth = 5;
            this.ctx.fillRect(
                centerX - width / 2 + segment.curve * 50 * perspective - edgeWidth,
                y,
                edgeWidth,
                20
            );
            this.ctx.fillRect(
                centerX + width / 2 + segment.curve * 50 * perspective,
                y,
                edgeWidth,
                20
            );
        }

        // 草地
        this.ctx.fillStyle = '#90EE90';
        this.ctx.fillRect(0, this.height * 0.3, this.width, this.height * 0.7);
    }

    updateUI() {
        document.getElementById('lap').textContent = `${this.lap} / ${this.maxLaps}`;

        const seconds = Math.floor(this.elapsedTime / 1000);
        const milliseconds = Math.floor((this.elapsedTime % 1000) / 100);
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        document.getElementById('time').textContent =
            `${minutes}:${secs.toString().padStart(2, '0')}.${milliseconds}`;

        document.getElementById('speed').textContent = Math.floor(this.player.speed * 10);

        // 順位を計算
        let position = 1;
        for (const opponent of this.opponents) {
            if (opponent.distance > this.player.distance) {
                position++;
            }
        }
        document.getElementById('position').textContent = `${position}位`;

        // アイテム表示
        if (this.playerItem) {
            const itemNames = {
                'speed': 'スピードアップ',
                'missile': 'ミサイル',
                'shield': 'シールド'
            };
            document.getElementById('item').textContent = itemNames[this.playerItem.type];
        } else {
            document.getElementById('item').textContent = 'なし';
        }
    }

    finish() {
        this.gameState = 'finished';

        let position = 1;
        for (const opponent of this.opponents) {
            if (opponent.distance > this.player.distance) {
                position++;
            }
        }

        const seconds = Math.floor(this.elapsedTime / 1000);
        const milliseconds = Math.floor((this.elapsedTime % 1000) / 100);
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        const timeString = `${minutes}:${secs.toString().padStart(2, '0')}.${milliseconds}`;

        document.getElementById('finalTime').textContent = timeString;
        document.getElementById('finalPosition').textContent = `${position}位`;
        document.getElementById('gameOver').classList.remove('hidden');
    }

    restart() {
        document.getElementById('gameOver').classList.add('hidden');
        this.gameState = 'start';
        this.lap = 1;
        this.elapsedTime = 0;
        this.playerItem = null;
        this.player = null;
        this.opponents = [];
        this.items = [];
        document.getElementById('startScreen').classList.remove('hidden');
    }
}

class Kart {
    constructor(x, y, color, isPlayer) {
        this.x = x;
        this.y = y;
        this.color = color;
        this.isPlayer = isPlayer;
        this.speed = 0;
        this.maxSpeed = 8;
        this.acceleration = 0.2;
        this.friction = 0.05;
        this.distance = 0;
        this.shield = false;
        this.stunned = false;
    }

    accelerate() {
        if (!this.stunned) {
            this.speed = Math.min(this.speed + this.acceleration, this.maxSpeed);
        }
    }

    brake() {
        this.speed = Math.max(this.speed - this.acceleration * 2, -this.maxSpeed / 2);
    }

    decelerate() {
        if (this.speed > 0) {
            this.speed = Math.max(this.speed - this.friction, 0);
        } else if (this.speed < 0) {
            this.speed = Math.min(this.speed + this.friction, 0);
        }
    }

    moveLeft() {
        if (!this.stunned) {
            this.x -= 5;
        }
    }

    moveRight() {
        if (!this.stunned) {
            this.x += 5;
        }
    }

    boost() {
        this.speed = this.maxSpeed * 1.5;
        setTimeout(() => {
            this.speed = Math.min(this.speed, this.maxSpeed);
        }, 2000);
    }

    hit() {
        if (this.shield) {
            this.shield = false;
            return;
        }

        this.stunned = true;
        this.speed *= 0.3;
        setTimeout(() => {
            this.stunned = false;
        }, 2000);
    }

    update(canvasWidth) {
        // 画面の境界チェック
        this.x = Math.max(50, Math.min(this.x, canvasWidth - 50));

        // 距離を更新
        this.distance += this.speed;
    }

    updateAI(canvasWidth) {
        // 簡単なAI
        this.accelerate();

        // ランダムに左右に動く
        if (Math.random() < 0.02) {
            this.x += (Math.random() - 0.5) * 10;
        }

        this.update(canvasWidth);

        // AIの距離を少しずつ増やす（プレイヤーとの競争）
        this.distance += this.speed * 0.95;
    }

    draw(ctx) {
        // シールドを描画
        if (this.shield) {
            ctx.strokeStyle = 'rgba(0, 255, 255, 0.5)';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(this.x, this.y, 35, 0, Math.PI * 2);
            ctx.stroke();
        }

        // カートの本体
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x - 20, this.y - 15, 40, 30);

        // タイヤ
        ctx.fillStyle = '#000000';
        ctx.fillRect(this.x - 25, this.y - 10, 8, 15);
        ctx.fillRect(this.x + 17, this.y - 10, 8, 15);
        ctx.fillRect(this.x - 25, this.y + 5, 8, 15);
        ctx.fillRect(this.x + 17, this.y + 5, 8, 15);

        // ドライバー（頭）
        ctx.fillStyle = '#ffd700';
        ctx.beginPath();
        ctx.arc(this.x, this.y - 5, 10, 0, Math.PI * 2);
        ctx.fill();

        // プレイヤーの場合、特別なマーク
        if (this.isPlayer) {
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('YOU', this.x, this.y + 35);
        }

        // スタンしている場合
        if (this.stunned) {
            ctx.fillStyle = '#ff0000';
            ctx.font = 'bold 16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('💫', this.x, this.y - 30);
        }
    }
}

class Item {
    constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.type = type; // speed, missile, shield
    }

    draw(ctx) {
        // アイテムボックス
        ctx.fillStyle = '#ffa500';
        ctx.fillRect(this.x - 15, this.y - 15, 30, 30);

        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;

        ctx.font = 'bold 20px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const symbols = {
            'speed': '⚡',
            'missile': '🚀',
            'shield': '🛡️'
        };

        ctx.strokeText(symbols[this.type], this.x, this.y);
        ctx.fillText(symbols[this.type], this.x, this.y);
    }
}

// ゲームを初期化
const game = new Game();
