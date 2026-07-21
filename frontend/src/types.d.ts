// src/types.d.ts
declare module 'tz-lookup' {
    /**
     * 根据经纬度获取 IANA 时区标识符
     * @param lat 纬度
     * @param lng 经度
     * @returns 时区字符串，如 'America/New_York'
     */
    function tzlookup(lat: number, lng: number): string;
    export = tzlookup;
  }