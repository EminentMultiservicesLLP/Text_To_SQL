using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Options;

namespace DataChat.Blazor;

/// <summary>Typed HTTP client for the local DataChat engine.</summary>
public sealed class DataChatClient(HttpClient http, IOptions<DataChatOptions> options)
{
    public bool IsEnabled => options.Value.Enabled;

    internal static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web)
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    };

    public async Task<ChatResponse> ChatAsync(ChatRequest request, CancellationToken ct = default)
    {
        if (!IsEnabled) return Error("The data assistant is switched off.");
        try
        {
            using var response = await http.PostAsJsonAsync("v1/chat", request, Json, ct);
            if (!response.IsSuccessStatusCode)
            {
                return Error($"The data assistant returned {(int)response.StatusCode} {response.ReasonPhrase}.");
            }
            return await response.Content.ReadFromJsonAsync<ChatResponse>(Json, ct) ?? Error("Empty response.");
        }
        catch (TaskCanceledException) when (!ct.IsCancellationRequested)
        {
            return Error("The data assistant took too long to answer.");
        }
        catch (HttpRequestException ex)
        {
            return Error($"The data assistant is not reachable ({ex.Message}).");
        }
    }

    public async Task SendFeedbackAsync(FeedbackRequest request, CancellationToken ct = default)
    {
        if (!IsEnabled) return;
        using var response = await http.PostAsJsonAsync("v1/feedback", request, Json, ct);
        response.EnsureSuccessStatusCode();
    }

    public async Task<ClientInfo?> GetClientInfoAsync(string clientId, CancellationToken ct = default)
    {
        if (!IsEnabled) return null;
        try
        {
            return await http.GetFromJsonAsync<ClientInfo>($"v1/clients/{Uri.EscapeDataString(clientId)}", Json, ct);
        }
        catch (HttpRequestException)
        {
            return null;
        }
    }

    private static ChatResponse Error(string text) => new() { Type = "error", Text = text };
}
