import RestClient from '../src/network/rest/restClient';
import { Address} from './../src/crypto';
import { PrivateKey } from './../src/crypto/PrivateKey';
import { WebsocketClient } from './../src/network/websocket/websocketClient';
import { signTransaction, makeInvokeTransaction} from './../src/transaction/transactionBuilder';
import { reverseHex, str2hexstr,sha256} from './../src/utils';
import { Parameter, ParameterType} from '../src/smartcontract/abi/parameter';
import { bigNumberify } from "ethers/utils";
const BN = require('bn.js');


describe('test_texasPoker', () => {
    const ONT_CONTRACT = '0000000000000000000000000000000000000001';
    const ONG_CONTRACT = '0000000000000000000000000000000000000002';
    const private1 = new PrivateKey('fe2e6bf548c30569185a5a70f6b7e7005b477f3e4164686a2758d2d765bb3485');
    const private2 = new PrivateKey('49855b16636e70f100cc5f4f42bc20a6535d7414fb8845e7310f8dd065a97221');
    const private3 = new PrivateKey('1094e90dd7c4fdfd849c14798d725ac351ae0d924b29a279a9ffa77d5737bd96');

    const address1 = new Address('ANTPeXCffDZCaCXxY9u2UdssB2EYpP4BMh');
    const address2 = new Address('AXK2KtCfcJnSMyRzSwTuwTKgNrtx5aXfFX');
    const address3 = new Address('AVXf5w8WD2y6jV1Lzi36oSKYNif1C7Surc');

    const codeHash = 'a564f3d516350b7accd0a83ad1b9d21f0d7f0405';

    const contractAddr = new Address(reverseHex(codeHash));
    // const Invoke = new scInvoke(contractAddr);
    const gasPrice = '500';
    const gasLimit = '200000';
    // const url = TEST_ONT_URL.REST_URL;
    // const url = 'http://127.0.0.1:'
    const url = 'http://polaris1.ont.io:';
    const restClient = new RestClient(url + '20334');
    const socketClient = new WebsocketClient(url + '20335');
    
    const attestClaimAvmCode = '';


    test('test_ifCheckIn', async() => {
        const method = 'ifCheckIn';
        const params = [
            new Parameter('account', ParameterType.ByteArray, address2.serialize())
        ];
        const tx = makeInvokeTransaction(method, params, contractAddr);
        const res = await restClient.sendRawTransaction(tx.serialize(), true);
        console.log(JSON.stringify(res));
        const val = res.Result.Result ? parseInt(reverseHex(res.Result.Result), 16) : 0;
        if (val > 0) {
            console.log('test_ifCheckIn ' + address1.toBase58() + ' can check in ');
        } else {
            console.log('test_ifCheckIn ' + address1.toBase58() + ' can NOT check in ');
        }
    });
    
    test('test_checkIn', async() => {
        const method = 'checkIn';
        const params = [
            new Parameter('account', ParameterType.ByteArray, address2.serialize())
        ];
        const tx = makeInvokeTransaction(method, params, contractAddr, gasPrice, gasLimit, address1);
        signTransaction(tx, private1);
        const response = await socketClient.sendRawTransaction(tx.serialize(), false, true);
        
        console.log('checkIn response is : ' + JSON.stringify(response));
        
    });
    test('test_sth', async() => {
        let salt1 = '0102';
        let salt2 = sha256(salt1);
        console.log('salt2 is ' + salt2);
        let salt3 = bigNumberify('0x' + salt2);

        let num1 = 30;
        let num2 = bigNumberify(num1).toHexString().slice(2);
        let num3 = sha256(num2);
        console.log('num2 is : ' + num2 );
        console.log('num3 is : ' + num3);

        const bn1 = new BN(reverseHex(salt2), 16);
        const bn2 = new BN(reverseHex(num3), 16);
        
        const bn3 = bn1.xor(bn2);
        console.log('bn3 is : ' + bn3);

        const bn4 = new BN(salt2, 16, 'le');
        const bn5 = new BN(num3, 16, 'le');
        const bn6 = bn4.xor(bn5);
        console.log(' bn4 = ' + bn4 + ', bn5 = ' + bn5);
        console.log(' bn6 is : ' + reverseHex(bn6.toString(16)));
        // const bn7 = bigNumberify(bn6);
        // console.log('bn7 is ' + bn7.toHexString());
    });
    test('test_startGame', async() => {
        const method = 'startGame';
        let pokerHashList: Parameter[] = [];
        const pokerNum = 54;
        const salt = 'salt';
        const saltToBeSha = str2hexstr(salt);
        console.log('saltToBeSha (hex string) is : ' + saltToBeSha);
        const shaSalt = sha256(saltToBeSha);
        const bnSalt = new BN(reverseHex(shaSalt), 16);
        console.log('shaSalt is : ' + shaSalt);
        for (let tmp = 0; tmp < pokerNum; tmp++ ) {
            // console.log('pokerHash'+ tmp.toString() + ': number = ' + tmp.toString(16) + ', sha256 = ' + sha256(tmp.toString(16)))
            let tmpBigNumber = bigNumberify(tmp);
            let tmpHexStrToBeSha = tmpBigNumber.toHexString().slice(2);
            let shaTmp = sha256(tmpHexStrToBeSha)
            let bnTmp = new BN(reverseHex(shaTmp), 16);
            const bnXorRes = bnTmp.xor(bnSalt);
            // console.log('bnXorRes is ' + bnXorRes.toString(16))
            const bigNumberRes = bigNumberify(bnXorRes.toString());
            // console.log(" if it is double : " + bigNumberRes.toHexString());
            
            const pokerHashTmp = reverseHex(bigNumberRes.toHexString().slice(2));
            // console.log('pokerHashTmp is : ' + pokerHashTmp)
            console.log('pokerHash'+ tmp.toString() + ': number = ' + tmpBigNumber.toNumber() + ', pokerHash = ' + pokerHashTmp);
            pokerHashList.push(new Parameter('pokerHash'+ tmpBigNumber.toNumber(), ParameterType.ByteArray, pokerHashTmp));
        }
        console.log('pokerHash list is ' + JSON.stringify(pokerHashList));
        const params = [
            new Parameter('pokerHashList', ParameterType.Array, pokerHashList),
            new Parameter('playerList', ParameterType.Array, [
                new Parameter('player1', ParameterType.ByteArray, address1.serialize()),
                new Parameter('player2', ParameterType.ByteArray, address2.serialize()),
                new Parameter('player3', ParameterType.ByteArray, address3.serialize())
            ]),
            new Parameter('gameId', ParameterType.Integer, 2)
        ];
        const tx = makeInvokeTransaction(method, params, contractAddr, gasPrice, gasLimit, address1);
        signTransaction(tx, private1);
        const response = await socketClient.sendRawTransaction(tx.serialize(), false, true);
        
        console.log('startGame response is : ' + JSON.stringify(response));
        
    });


    test('test_endGame', async () => {
        const method = 'endGame';
        const salt = 'salt';
        const params = [
            new Parameter('gameId', ParameterType.Array, 2),
            new Parameter('salt', ParameterType.ByteArray, str2hexstr(salt))
        ];
        const tx = makeInvokeTransaction(method, params, contractAddr, gasPrice, gasLimit, address1);
        signTransaction(tx, private1);
        const response = await socketClient.sendRawTransaction(tx.serialize(), false, true);
        
        console.log('startGame response is : ' + JSON.stringify(response));
    });

    test('test_checkPokerHash', async () => {
        const method = 'checkPokerHash';
        const params = [
            new Parameter('gameId', ParameterType.Array, 2),
            new Parameter('pokerNum', ParameterType.Integer, 30)
        ];
        const tx = makeInvokeTransaction(method, params, contractAddr);
        const res = await restClient.sendRawTransaction(tx.serialize(), true);
        // the res should be equal to 'f515c389ade4dba9d3a84eeadd8954377cd5dc2d4a642941db6adc1fc797f4ed'
        console.log('checkPokerHash, res is ' + JSON.stringify(res));
    });




});

