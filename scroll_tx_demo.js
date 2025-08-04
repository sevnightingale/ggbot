const { ethers } = require('ethers');

// Configuration
const RPC_URL = 'https://sepolia-rpc.scroll.io';
const PRIVATE_KEY = '0x89df88ab8019059a0ee79712da192a15e1650b787c9975d9babc87ffd1553710';
const MESSAGE = 'Hello from ggbots autonomous trading platform on Scroll! 🤖📈';

async function sendMessageTransaction() {
    console.log('🚀 Sending ggbots message to Scroll blockchain...\n');
    
    try {
        // Connect to Scroll Sepolia
        const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
        const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
        
        console.log('📧 Wallet Address:', wallet.address);
        
        // Check balance
        const balance = await wallet.getBalance();
        console.log('💰 Balance:', ethers.utils.formatEther(balance), 'ETH\n');
        
        // Convert message to hex data
        const messageHex = ethers.utils.hexlify(ethers.utils.toUtf8Bytes(MESSAGE));
        console.log('📝 Message:', MESSAGE);
        console.log('🔢 Message as hex:', messageHex, '\n');
        
        // Create transaction
        const tx = {
            to: wallet.address, // Send to self
            value: ethers.utils.parseEther('0.001'), // Small amount
            data: messageHex, // Our message!
            gasLimit: 50000, // Higher gas limit for data
        };
        
        console.log('📤 Sending transaction...');
        const txResponse = await wallet.sendTransaction(tx);
        
        console.log('✅ Transaction sent!');
        console.log('🔗 Transaction Hash:', txResponse.hash);
        console.log('🌐 View on Scroll Sepolia:', `https://sepolia.scrollscan.dev/tx/${txResponse.hash}`);
        
        console.log('\n⏳ Waiting for confirmation...');
        const receipt = await txResponse.wait();
        
        console.log('🎉 Transaction confirmed!');
        console.log('⛽ Gas used:', receipt.gasUsed.toString());
        console.log('📊 Block number:', receipt.blockNumber);
        
        return txResponse.hash;
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        return null;
    }
}

// Run the demo
sendMessageTransaction().then(hash => {
    if (hash) {
        console.log('\n🏆 HACKATHON DEMO SUCCESS!');
        console.log('🔗 Share this transaction link:');
        console.log(`   https://sepolia.scrollscan.dev/tx/${hash}`);
        console.log('\n✨ This proves ggbots can execute transactions on Scroll blockchain!');
    }
});