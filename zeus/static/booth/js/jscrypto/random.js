
/*
 * Random Number generation, now uses the glue to Java
 */

Random = {};

Random.GENERATOR = null;

Random.getRandomInteger = function(max) {
  var bit_length = max.bitLength();
  var random;
  if (!sjcl.random.__entropySet) { console && console.error && console.error("uninitialized random entropy"); }
  random = sjcl.random.randomWords(bit_length / 32, 0);
  // we get a bit array instead of a BigInteger in this case
  var rand_bi = new BigInt(sjcl.codec.hex.fromBits(random), 16);
  return rand_bi.mod(max);
};

