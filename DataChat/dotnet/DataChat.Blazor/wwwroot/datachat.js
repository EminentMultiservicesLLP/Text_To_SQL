// Saves a file built on the server (CSV / Excel export of an answer's table) in the user's browser.
export async function downloadFile(fileName, contentType, streamRef) {
    const buffer = await streamRef.arrayBuffer();
    const url = URL.createObjectURL(new Blob([buffer], { type: contentType }));
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}
