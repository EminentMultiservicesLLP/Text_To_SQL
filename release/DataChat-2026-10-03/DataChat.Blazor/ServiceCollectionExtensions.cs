using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;

namespace DataChat.Blazor;

public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Registers the DataChat client. Bind from configuration, e.g.
    /// <c>builder.Services.AddDataChat(builder.Configuration.GetSection("DataChat"));</c>
    /// </summary>
    public static IServiceCollection AddDataChat(this IServiceCollection services, IConfiguration section)
    {
        services.Configure<DataChatOptions>(section);
        return services.AddDataChatCore();
    }

    public static IServiceCollection AddDataChat(this IServiceCollection services, Action<DataChatOptions> configure)
    {
        services.Configure(configure);
        return services.AddDataChatCore();
    }

    private static IServiceCollection AddDataChatCore(this IServiceCollection services)
    {
        services.AddHttpClient<DataChatClient>((sp, http) =>
        {
            var o = sp.GetRequiredService<IOptions<DataChatOptions>>().Value;
            http.BaseAddress = new Uri(o.BaseUrl.EndsWith('/') ? o.BaseUrl : o.BaseUrl + "/");
            http.Timeout = TimeSpan.FromSeconds(o.TimeoutSeconds);
            if (!string.IsNullOrEmpty(o.ApiKey))
            {
                http.DefaultRequestHeaders.Add("X-Api-Key", o.ApiKey);
            }
        });
        return services;
    }
}
