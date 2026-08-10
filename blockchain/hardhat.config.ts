import '@nomicfoundation/hardhat-toolbox';
import type { HardhatUserConfig } from 'hardhat/config';

const accounts = process.env.LEDGER_SIGNER_PRIVATE_KEY ? [process.env.LEDGER_SIGNER_PRIVATE_KEY] : [];
const config: HardhatUserConfig = {
  solidity: { version: '0.8.28', settings: { optimizer: { enabled: true, runs: 500 }, viaIR: true } },
  networks: {
    localhost: { url: process.env.LEDGER_RPC_URL ?? 'http://127.0.0.1:8545', accounts },
    besu: { url: process.env.LEDGER_RPC_URL ?? 'http://besu-rpc:8545', accounts, chainId: Number(process.env.LEDGER_CHAIN_ID ?? '1337') },
    base: { url: process.env.LEDGER_RPC_URL ?? 'https://mainnet.base.org', accounts, chainId: Number(process.env.LEDGER_CHAIN_ID ?? '8453') },
  },
};
export default config;
