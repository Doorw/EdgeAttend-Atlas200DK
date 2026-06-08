export async function uploadImageAndGetCount(formData) {
    // 这里假设后端API地址是 /api/predict
    // 实际使用时需要替换为真实的后端地址

    const apiBaseUrl = 'http://localhost:5000';  // 后端服务器地址
    const response = await fetch(`${apiBaseUrl}/api/predict`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error('服务器错误');
    }

    return await response.json();
}
export async function uploadImageAndGetClassCount(formData) {
    // 这里假设后端API地址是 /api/predict
    // 实际使用时需要替换为真实的后端地址

    const apiBaseUrl = 'http://localhost:5000';  // 后端服务器地址
    const response = await fetch(`${apiBaseUrl}/api/predict`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error('服务器错误');
    }

    return await response.json();
}
