import { expect } from 'chai';
import { ethers } from 'hardhat';

describe('IntegrityAnchor', function () {
  it('anchors once and exposes the immutable commitment', async function () {
    const [admin, writer] = await ethers.getSigners();
    const factory = await ethers.getContractFactory('IntegrityAnchor');
    const contract = await factory.deploy(admin.address, writer.address);
    const tenant = ethers.keccak256(ethers.toUtf8Bytes('opaque-tenant'));
    const batch = ethers.keccak256(ethers.toUtf8Bytes('opaque-batch'));
    const root = ethers.keccak256(ethers.toUtf8Bytes('merkle-root'));
    const kind = ethers.encodeBytes32String('audit');
    await expect(contract.connect(writer).anchor(tenant,batch,root,kind,10)).to.emit(contract,'RootAnchored');
    expect(await contract.exists(root)).to.equal(true);
    await expect(contract.connect(writer).anchor(tenant,batch,root,kind,10)).to.be.reverted;
  });

  it('rejects unauthorised writers', async function () {
    const [admin, writer, outsider] = await ethers.getSigners();
    const factory = await ethers.getContractFactory('IntegrityAnchor');
    const contract = await factory.deploy(admin.address, writer.address);
    await expect(contract.connect(outsider).anchor(ethers.ZeroHash,ethers.ZeroHash,ethers.id('root'),ethers.encodeBytes32String('audit'),1)).to.be.reverted;
  });
});
