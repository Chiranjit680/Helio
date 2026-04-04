const {pipeline} = require("@xenova/transformers");
let embedder = null;

const initEmbedder = async () => {
    console.log("Loading MiniLM-L6-v2 embedding model...");
    embedder = await pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2");
    console.log(" ✅ MiniLM-L6-v2 embedding model loaded successfully.");
}

const generateEmbedding = async (text) => {
    if(!embedder){
        throw new Error("Embedder not initialised - call initEmbedder() first");
    }

    const output = await embedder(text, {
        pooling: "mean",
        normalize: true,
    });

    return Array.from(output.data);
};

module.exports = {
    initEmbedder,
    generateEmbedding,
};
