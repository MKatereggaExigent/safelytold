import { ethers } from 'hardhat';
import { writeFile } from 'node:fs/promises';

async function main() {
  const [deployer] = await ethers.getSigners();
  const admin = process.env.LEDGER_ADMIN_ADDRESS ?? deployer.address;
  const writer = process.env.LEDGER_WRITER_ADDRESS ?? deployer.address;
  const factory = await ethers.getContractFactory('IntegrityAnchor');
  const contract = await factory.deploy(admin, writer);
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  const network = await ethers.provider.getNetwork();
  const output = { address, chainId: network.chainId.toString(), deployedBy: deployer.address };
  await writeFile('deployment.local.json', JSON.stringify(output, null, 2));
  console.log(JSON.stringify(output));
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
