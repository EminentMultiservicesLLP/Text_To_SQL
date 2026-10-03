namespace DataChat.Blazor;

public sealed class DataChatOptions
{
    /// <summary>False hides the chat everywhere and sends nothing to the engine (switch off per environment).</summary>
    public bool Enabled { get; set; } = true;

    /// <summary>Engine address on this server, e.g. http://127.0.0.1:8765/</summary>
    public string BaseUrl { get; set; } = "http://127.0.0.1:8765/";

    /// <summary>Must match DATACHAT_API_KEY in the engine's .env.</summary>
    public string ApiKey { get; set; } = "";

    /// <summary>Default client pack, e.g. bellona_rista. A component parameter can override it.</summary>
    public string ClientId { get; set; } = "";

    /// <summary>Includes the time a CPU-only local model may need when the fallback is enabled.</summary>
    public int TimeoutSeconds { get; set; } = 90;
}
